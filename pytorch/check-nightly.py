#!/usr/bin/env python3

# This script checks the status of recent pytorch nightly build status

import re
import os
import requests
import argparse
import subprocess
from tabulate import tabulate
import itertools
import urllib.parse
from datetime import date, timedelta
from dataclasses import dataclass
from bs4 import BeautifulSoup
from collections import defaultdict
from packaging.version import parse

DEFAULT_RESULT_LIMIT = 10

def memoize(function):
    """
    """
    call_cache = {}

    def memoized_function(*f_args):
        if f_args in call_cache:
            return call_cache[f_args]
        call_cache[f_args] = result = function(*f_args)
        return result
    return memoized_function

@dataclass
class TorchNightlyWheel:
    name: str
    version: str
    url: str

# Get nightly html and save it to a path
# ../torchaudio-0.9.0.dev20210315-cp36-cp36m-macosx_10_9_x86_64.whl
@memoize
def get_nightly_html(cuda_version: str):
    PYTORCH_NIGHTLY_BASE = f"https://download.pytorch.org/whl/nightly/{cuda_version}/"
    r = requests.get(PYTORCH_NIGHTLY_BASE + "torch_nightly.html")
    r.raise_for_status()
    data = r.text
    soup = BeautifulSoup(data, 'html.parser')
    out = defaultdict(dict)
    results = []
    for link in soup.find_all('a'):
        text = urllib.parse.unquote(link.text)
        full_url = os.path.join(PYTORCH_NIGHTLY_BASE, text)
        results.append(full_url)
    return results

# def filter_results(fulldata, os = "linux", pyver = None, limit = DEFAULT_RESULT_LIMIT):
#     # Filter results from full_data
#     dates = sorted(fulldata.keys(), reverse=True)
#     results = defaultdict(dict)
#     pyver = "" if not pyver else pyver
#     for index, date in enumerate(dates):
#         if index == limit:
#             break
#         wheels = fulldata[date]
#         for pkgname in wheels:
#             pkgs = wheels[pkgname]
#             for pkg in pkgs:
#                 if os in pkg.platform and pyver in pkg.pyver:
#                     pkg_fullname = pkg.fullname
#                     results[date][pkg_fullname] = pkg
#     return results

# def visualize(filtered_data):
#     pkgs = ["torch", "torchvision", "torchaudio", "torchcsprng"]
#     pyvers = ["36", "37", "38", "39"]
#     # platforms = ["linux_x86_64", "macosx_10_9_x86_64", "win_amd64"]
#     platforms = ["linux_x86_64"]
#     result = [["Package"]]
#     left_header_pkg = []
#     for element in itertools.product(pkgs, pyvers, platforms):
#         left_header_pkg.append(f"{element[0]}-py{element[1]}-{element[2]}")
#     for pkg in left_header_pkg:
#         result.append([])
#         result[-1].append(pkg)
#     for date in filtered_data:
#         result[0].append(date)
#         for pkg_index, pkg in enumerate(left_header_pkg):
#             if pkg in filtered_data[date]:
#                 result[pkg_index+1].append("Success")
#             else:
#                 result[pkg_index+1].append("Failed")
#     return result

def get_normalized_version(url: str) -> str:
    return re.sub(
            r"%2B.*",
            "",
            "-".join(os.path.basename(url).split("-")[:2])
    )

def get_version(url: str) -> str:
    return os.path.basename(url).split("-")[1]

def satisfy_condition(url: str, day: str, pyver: str, platform: str):
    base = os.path.splitext(os.path.basename(url))[0].split("-")
    name = base[0]
    version = base[1]
    pyver_url = base[2]
    platform_url = base[-1]
    return (day in version) and (pyver in pyver_url) and (platform in platform_url)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Check recent pytorch nightly builds")
    parser.add_argument('--cuda', type=str, required=True,
                        help="CUDA version pytorch is built against")
    parser.add_argument('--pyver', type=str, default="cp37",
                        help="Python version pytorch is built against")
    parser.add_argument('--os', type=str, default="linux",
                        help="Operating system pytorch is built against")
    parser.add_argument('--limit', type=str, default=10,
                        help="Return the most recent <limit> results")
    args = parser.parse_args()
    full_data = get_nightly_html(args.cuda)
    # Generate the result of last five days
    days = []
    today = date.today()
    for _ in range(0, 5):
        days.append(today.strftime("%Y%m%d"))
        today = today - timedelta(days=1)
    results = { }
    for day in days:
        results[day] = []
        for url in full_data:
            if satisfy_condition(url, day = day, pyver = args.pyver, platform = args.os):
                results[day].append(url)
    for day in days:
        print(f"{day}")
        for url in results[day]:
            print(f"\t- {os.path.basename(url)}")
