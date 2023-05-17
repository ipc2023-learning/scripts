#!/usr/bin/env python3

import argparse
from pathlib import Path
import random
import shutil
from subprocess import check_call, CalledProcessError
import time

from lab.tools import Properties


def sort_run_dir(run_dir, logs_dir):
    props = Properties(str(run_dir / "static-properties"))
    algorithm = props["algorithm"]
    experiment = props["experiment_name"]
    target = logs_dir/f"logs-{algorithm}"/experiment/run_dir.parent.name/run_dir.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(run_dir, target)
    uncompressed_files = ["properties", "static-properties", "values.log", "watch.log"]
    compressed_files = []
    for f in target.glob("*"):
        if f.name not in uncompressed_files:
            compressed_files.append(f)
    tar_filename = "other_files.tgz"
    tar_cmd = ["tar", "-czf", str(tar_filename)] + [f.name for f in compressed_files]
    check_call(tar_cmd, cwd=target)
    for path in compressed_files:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

def sort_experiment(exp_dir, logs_dir):
    for run_dir in exp_dir.glob("runs-*/*"):
        sort_run_dir(run_dir, logs_dir)

def commit_dirs(logs_dir):
    for repo in logs_dir.glob("*"):
        check_call(["git", "add", "--all"], cwd=repo)
        try:
            check_call(["git", "commit", "-m", "Add logs"], cwd=repo)
        except CalledProcessError:
            pass # nothing to commit
        while True:
            try:
                check_call(["git", "push", "-u", "origin", "main"], cwd=repo)
                break
            except CalledProcessError:
                print(f"Could not push {repo}")
                time.sleep(random.random()*60)

def create_repos(images_dir, logs_dir):
    for image in images_dir.glob("*.img"):
        repo = f"ipc2023-classical/logs-{image.stem}"
        print(f"Creating repo '{repo}'")
        check_call(["gh", "repo", "create", f"{repo}", "--private"])
        check_call(["gh", "repo", "clone", f"{repo}"], cwd=logs_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create")
    parser.add_argument("--sort")
    parser.add_argument("--commit", action="store_true")
    logs_dir = Path("logs")
    args = parser.parse_args()
    if args.create:
        create_repos(Path(args.create), logs_dir)
    if args.sort is not None:
        sort_experiment(Path(args.sort), logs_dir)
    if args.commit:
        commit_dirs(logs_dir)
