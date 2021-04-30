"""
Run specified PyTorch abtest on a machine
"""
import os
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

def run_script(script_file: str) -> str:
    command = ["sudo", "-E", "systemd-run", "--slice=workload.slice", "--same-dir",
               "--wait", "--collect", "--service-type=exec", "--pty", f'--uid={os.environ["USER"]}',
               "bash", script_file]
    output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode().strip()
    return output

def run_group(repo: git.Repo, commit: str, script: str):
    # Checkout the commit
    checkout_commit(repo, commit)
    # Build the repo
    build_repo(repo)
    # Run the script
    output = run_script(script)
    # Save output to the directory
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run abtest on a devbig machine")
    parser.add_argument("--pytorch", required=True, type=str)
    parser.add_argument("--control", required=True, type=str)
    parser.add_argument("--treatment", required=True, type=str)
    parser.add_argument("--script", required=True, type=str)
    parser.add_argument("--output", required=True, type=str)
    args = parser.parse_args()
    pytorch_repo = git.Repo(args.pytorch)
    o1 = run_group(pytorch_repo, args.control, args.script)
    o2 = run_group(pytorch_repo, args.treatment, args.script)
    o = f"===================== CONTROL GROUP OUTPUT ================\n{o1}\n"
    o += f"===================== TREATMENT GROUP OUTPUT ===================\n{o2}\n"
    with open(args.output, "w") as fo:
        fo.write(o)
