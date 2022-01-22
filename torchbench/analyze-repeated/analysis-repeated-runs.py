#!/usr/bin/env python
"""
Script the analyze repeated runs of TorchBench results.

It performs stableness analysis results of a list of result json files:
1. test filter of unstable tests across runs
2. norm file in YAML format for score generation
3. details of each unstable test in csv format

stable == True iff max_delta(test) <= THRESHOLD
max_delta(test) = (max(test) - min(test)) / min(test),
where test is the median latency of all runs.
"""

import os
import re
import sys
import json
import yaml
import argparse
from numpy import median
from dataclasses import dataclass
from typing import List

DEFAULT_THRESHOLD = 0.07

def get_max_delta(latencies):
    return (max(latencies) - min(latencies)) / min(latencies)

def parse_test_name(test):
    regex = "test\_(.*)\[(.*)-(.*)-(.*)\]"
    return re.match(regex, test).groups()

@dataclass
class TorchBenchTest:
    # name of the test
    name: str
    # How many times did this test run
    run_times: int
    # median latency
    median: float
    # (max-min) / min
    max_delta: float
    # variance
    variance: float
    # latencies
    latencies: List[float]
    # device: cpu or cuda
    device: str
    def __init__(self, name, latencies):
        if "cpu" in name:
            self.device = "cpu"
        elif "cuda" in name:
            self.device = "cuda"
        else:
            print(f"Unrecognized device name for test {name}")
            exit(0)
        self.name = name
        self.latencies = latencies
        self.run_times = len(latencies)
        self.max_delta = (max(latencies) - min(latencies)) / min(latencies)
        self.variance = (max(latencies) - min(latencies)) / ((max(latencies) + min(latencies)) / 2)
        self.median = median(latencies)

def isvalidjson(result_dir, x):
    return x.endswith(".json") and os.path.getsize(os.path.join(result_dir, x))

def get_result_jsons(result_dir):
    results = []
    for json_file in filter(lambda x: isvalidjson(result_dir, x), os.listdir(result_dir)):
        r = os.path.join(result_dir, json_file)
        with open(r, "r") as jf:
            results.append(json.load(jf))
    return results

def dump_single_test(alltests):
    result = []
    head = ["name", "device", "run_times", "median", "max_delta", "variance"]
    result.append(",".join(head))
    for t in alltests:
        value = []
        for h in head:
            value.append(str(getattr(t, h)))
        result.append(",".join(value))
    return "\n".join(result)

def dump_unstable_result(r, tp='single'):
    result = []
    head = ["name", "max_delta", "type"]
    result.append(",".join(head))
    for t in r:
        value = [t, str(r[t]), tp]
        result.append(",".join(value))
    return "\n".join(result)

def analysis_single_json(json_obj):
    all_tests = []
    for test in json_obj["benchmarks"]:
        tname = test["name"]
        tlatencies = test["stats"]["data"]
        t = TorchBenchTest(name=tname, latencies=tlatencies)
        if t.name:
            all_tests.append(t)
    return all_tests

# Return:
# union of unstable tests within a run
# unstable tests across runs
def analysis_multiple_results(results, threshold=THRESHOLD):
    # get union of unstable tests of all runs
    unstable_results = []
    unstable_singlerun = {}
    for r in results:
        unstable_results.extend(list(filter(lambda t: t.max_delta >= threshold, r)))
    for t in unstable_results:
        if not t.name in unstable_singlerun:
            unstable_singlerun[t.name] = t.max_delta
        else:
            unstable_singlerun[t.name] = max(unstable_singlerun[t.name], t.max_delta)
    # get unstable tests across runs using median
    test_medians = {}
    unstable_crossrun = {}
    for r in results:
        for t in r:
            if t.name not in test_medians:
                test_medians[t.name] = []
            test_medians[t.name].append(t.median)
    for name in test_medians:
        max_delta = get_max_delta(test_medians[name])
        if max_delta >= threshold:
            unstable_crossrun[name] = max_delta
    return (unstable_singlerun, unstable_crossrun)

def stableness_analysis(results, base_threshold=0.01, step=0.01, num_steps=11):
    r = {}
    for ns in range(num_steps):
        threshold = base_threshold + step * ns
        unstable_singlerun, unstable_crossrun = analysis_multiple_results(results, threshold=threshold)
        r[threshold] = unstable_crossrun.keys()
    return r

def dump_stable_analysis_results(tests, r):
    ret = ""
    common_tests = len(get_common_tests(tests))
    for t in r:
        ret += f"{t},{common_tests - len(r[t])},{len(r[t])}\n"
    return ret

def gen_filter_for_tests(tests):
    p = []
    for t in tests:
        parts = list(parse_test_name(t))
        pp = " and ".join(parts)
        p.append(f"({pp})")
    concat = " or ".join(p)
    return f"(not ({concat}))"

# we only include tests that are covered in all runs
def get_common_tests(results):
    n = list(map(lambda x: x.name, results[0]))
    for r in results:
        nn = list(map(lambda x: x.name, results[0]))
        n = [val for val in n if val in nn]
        if not len(n) == len(nn):
            print("mismatching tests...")
            exit(1)
    return n

# Norm should contain tests that:
# 1. exist in all repeated runs
# 2. does not exist in unstable_tests list
def gen_norm(results, unstable_tests):
    tests = get_common_tests(results)
    d = {}
    for t in tests:
        d[t] = []
        for r in results:
            x = list(filter(lambda v: v.name == t, r))
            assert len(x) == 1 , f"can't find test {t}"
            d[t].append(x[0].median)
    ret = {}
    for t in tests:
        ret[t] = {}
        ret[t]["norm"] = float(median(d[t]))
        if t in unstable_tests:
            ret[t]["stable"] = False
        else:
            ret[t]["stable"] = True
    return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stable-threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="Threshold to filter unstable tests")
    parser.add_argument("--result-dir", required=True, help="Directory that contains pytest json files")
    parser.add_argument("--output-dir", required=True, help="Directory that saves the analysis results")
    args = parser.parse_args()
    json_objs = get_result_jsons(result_dir)
    single_results = list(map(lambda x: analysis_single_json(x), json_objs))
    sa = stableness_analysis(single_results)
    # print(dump_stable_analysis_results(single_results, sa))
    unstable_sr, unstable_cr = analysis_multiple_results(single_results)
    # dump unstable tests
    r1 = dump_unstable_result(unstable_sr, tp='single')
    r2 = dump_unstable_result(unstable_cr, tp='cross')
    # print(r1)
    print(r2)
    # generate filter for unstable tests
    test_filter = gen_filter_for_tests(unstable_cr.keys())
    # print(test_filter)
    # generate norm file
    norm = gen_norm(single_results, unstable_cr.keys())
    data = yaml.dump(norm)
    # print(data)
