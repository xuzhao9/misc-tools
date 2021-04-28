"""
Run specified PyTorch abtest on a machine
"""

import argparse
import git
import subprocess

def checkout_commit(repo: git.Repo, commit: str):
    repo.git.checkout(commit)
    # Update submodules
    for submodule in repo.submodules:
        submodule.update(init=True)

def build_repo(repo: git.Repo):
    command = ["python", "setup.py", "install"]
    subprocess.check_call(command, cwd=repo.working_tree_dir)

def run_script(script_file: str):
    command = ["sudo", "-E", "systemd-run", "--slice=workload.slice", "--same-dir",
               "--wait", "--collect", "--service-type=exec", "--pty", f'--uid={os.environ["USER"]}',
               "bash", script_file]
    subprocess.check_call(command)

def run_group(repo: git.Repo, commit: str. script: str):
    # Checkout the commit
    checkout_commit(repo, commit)
    # Build the repo
    build_repo(repo)
    # Run the script
    run_script(script_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run abtest on a devbig machine")
    parser.add_argument("--pytorch", required=True, type=str)
    parser.add_argument("--control", required=True, type=str)
    parser.add_argument("--treatment", required=True, type=str)
    parser.add_argument("--script", required=True, type=str)
    args = parser.parse_args()
    pytorch_repo = git.Repo(args.pytorch)
    run_group(pytorch_repo, args.control, args.script)
    run_group(pytorch_repo, args.treatment, args.script)
