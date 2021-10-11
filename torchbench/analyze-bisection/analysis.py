import os
import json
import itertools
import yaml
from bokeh.palettes import Category10
from bokeh.models import HoverTool, Div, Range1d, HoverTool
from bokeh.plotting import figure, output_file, show
from tabulate import tabulate
from datetime import datetime as dt

WORKDIR = "results/"
BISECTION_RESULTS = "bisections-v2/"
RECENT_DAYS = 7
THRESHOLD = 7

def build_result_db(workdir):
    # key: pytorch_version, value: json file path and obj
    db = {}
    # For each json file
    for fname in filter(lambda x: x.endswith(".json"), sorted(os.listdir(workdir))):
        filepath = os.path.join(workdir, fname)
        with open(filepath, "r") as jfile:
            jdata = json.load(jfile)
        torchver = jdata["machine_info"]["pytorch_version"]
        if "dev" in torchver:
            torchver = torchver.split("dev", 1)[1]
        if torchver not in db:
            db[torchver] = []
        db[torchver].append((jfile, jdata, torchver))
    return db

def get_means(data):
    rc = dict()
    for param in data["benchmarks"]:
        name = param["name"]
        mean = param["stats"]["mean"]
        rc[name] = mean
    return rc

def beautify_bisection_result(result, testset):
    output_str = [['Benchmark']]
    for t in testset:
        c = []
        c.append(t)
        output_str.append(c)
    for k in result:
        output_str[0].append(k) 
        for index, t in enumerate(testset):
            output_str[index+1].append(result[k][t])
    return tabulate(output_str, headers='firstrow')

def get_testset(jdata):
    results = []
    for param in jdata["benchmarks"]:
        results.append(param["name"])
    return results

def gen_perf_signals(db):
    signals = {}
    db_keys = sorted(db.keys())
    testset = []
    # Generate the test list
    for key in db_keys:
        # Use the latest result
        test = db[key][-1][1]
        cur_testset = get_testset(test)
        if not testset:
            testset = get_testset(test)
        else:
            testset = list(set(testset) & set(cur_testset))

    for key in db_keys:
        test = db[key][-1]
        means = get_means(test[1])
        testcase = {}
        for t in testset:
            testcase[t] = means[t]
        signals[key] = testcase
    return signals, testset

# Construct the bisection config
def gen_bisection_config(signal):
    bconfig = {}
    bconfig["direction"] = "both"
    bconfig["threshold"] = THRESHOLD
    bconfig["timeout"] = 120
    bconfig["start_version"] = signal["testa_data"]["machine_info"]["pytorch_version"]
    bconfig["start"] = signal["testa_data"]["machine_info"]["pytorch_git_version"]
    bconfig["end_version"] = signal["testb_data"]["machine_info"]["pytorch_version"]
    bconfig["end"] = signal["testb_data"]["machine_info"]["pytorch_git_version"]
    bconfig["tests"] = []
    for test in signal["perf_signals"]:
        bconfig["tests"].append(test[0])
    bconfig["details"] = {}
    for test in signal["perf_signals"]:
        bconfig["details"][test[0]] = {}
        bconfig["details"][test[0]]["before"] = test[1]
        bconfig["details"][test[0]]["after"] = test[2]
        bconfig["details"][test[0]]["delta"] = test[4]
    return bconfig

def gen_bisection_configs(signals, bisection_root):
    for signal in signals:
        bisection_dir = os.path.join(bisection_root, f"bisection_{signal['testb']}")
        os.makedirs(bisection_dir, exist_ok=True)
        with open(os.path.join(bisection_dir, "config.yaml"), "w") as bconfig:
            bisection_obj = gen_bisection_config(signal)
            bconfig.write(yaml.dump(bisection_obj))

def visualize_perf_signals(signals):
    plot_height = 800
    plot_width = 1000
    dates = []
    keys = {}
    signals = signals[-RECENT_DAYS:]
    for s in signals:
        signal = s["perf_signals"]
        pytorch_ver = s["testb"]
        pytorch_ver_cuda_loc = pytorch_ver.rfind('+')
        pytorch_ver = pytorch_ver[:pytorch_ver_cuda_loc]
        dates.append(dt.strptime(pytorch_ver, "%Y%m%d"))
        for ss in signal:
            if ss[0] not in keys:
                keys[ss[0]] = 1
            else:
                keys[ss[0]] += 1
    selected_keys = {}
    for k in keys:
        if keys[k] < 10:
            selected_keys[k] = []
    # Draw the new trend graph
    # TODO Filter: only shows the top X tests that has the most variance
    colors = itertools.cycle(Category10[10])

    for index, s in enumerate(signals):
        signal = s["perf_signals"]
        signal_dict = {}
        for ss in signal:
            signal_dict[ss[0]] = ss[4] / 100.0
        for rs in selected_keys:
            if rs not in signal_dict:
                selected_keys[rs].append(0.0)
            else:
                selected_keys[rs].append(signal_dict[rs])
    p = figure(plot_width=plot_width, plot_height=plot_height,
               x_axis_type='datetime')
    for sk in list(selected_keys.keys()):
        scores = selected_keys[sk]
        color = next(colors)
        p.line(dates, scores, color=color, line_width=2, legend_label=sk)

    p.y_range = Range1d(-1.0, 1.0)
    p.legend.location = "bottom_right"
    output_file("plot_details.html")
    show(p)

if __name__ == "__main__":
    db = build_result_db(WORKDIR)
    signals, testset = gen_perf_signals(db)
    signals_output = beautify_bisection_result(signals, testset)
    print(signals_output)
    # visualize_perf_signals(signals)

    # Generate bisection configs
    gen_bisection_configs(signals, BISECTION_RESULTS)
