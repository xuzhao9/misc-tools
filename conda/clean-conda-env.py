#!/usr/bin/env python3

import re
import argparse
import fnmatch
import subprocess
from typing import List

def get_conda_envs() -> List[str]:
    commands = ['conda', 'env', 'list']
    out = subprocess.check_output(commands).decode().strip()
    envs = []
    for line in out.splitlines():
        if not line.startswith("#"):
            env_name = re.search("(.*?)\s", line)[1]
            envs.append(env_name)
    return envs

# Remove the given environments
def remove_conda_envs(envs: List[str]):
    command = ['conda', 'env', 'remove', '--name']
    for env in envs:
        local_command = command.copy()
        local_command.append(env)
        print(f"Removing conda environment: {env} ...", end="")
        subprocess.check_call(local_command,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        print("Done")

# Remove conda environments matching the given regex
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Remove conda envs matching glob")
    parser.add_argument('--glob', type=str, required=True,
                        help="The glob to match envs to remove.")
    parser.add_argument('--yes', action='store_true',
                        help="Do not ask for confirmation before removing envs.")
    args = parser.parse_args()
    conda_envs = get_conda_envs()
    filtered_envs = fnmatch.filter(conda_envs, args.glob)
    if not len(filtered_envs):
        print(f"Don't find specifed environment matching glob \"{args.glob}\", all environments: {conda_envs}.")
        exit()
    if not args.yes:
        print(f"I am going to remove the following conda envs: {filtered_envs}, continue [y/N]? ", end='')
        choice = input().lower().strip()
        if not choice == 'y' or choice == 'yes':
            print("No conda env is removed.")
            exit()
    # Now remove the envs
    remove_conda_envs(filtered_envs)

