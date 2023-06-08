#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil
from subprocess import check_call

from lab.tools import Properties


def sort_run_dir(run_dir, logs_dir):
    print(f"Fetching data from {run_dir}")
    props = Properties(str(run_dir / "static-properties"))
    algorithm = props["algorithm"]
    experiment = props["experiment_name"]
    target = logs_dir/f"{algorithm}"/experiment/run_dir.parent.name/run_dir.name
    target.mkdir(parents=True, exist_ok=True)
    uncompressed_files = {"properties", "static-properties", "driver.log", "run", "run.err", "run.log", "values.log", "watch.log"}
    compressed_files = []
    for f in run_dir.glob("*"):
        if f.name not in uncompressed_files:
            compressed_files.append(f)
    tar_filename = target / "other_files.tgz"
    tar_cmd = ["tar", "-czf", str(tar_filename)] + [f.name for f in compressed_files]
    check_call(tar_cmd, cwd=run_dir)
    for path in uncompressed_files:
        if (run_dir / path).exists():
            shutil.copy2(run_dir / path, target)


def sort_experiment(exp_dir, logs_dir):
    for run_dir in sorted(exp_dir.glob("runs-*/*")):
        sort_run_dir(run_dir, logs_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_dir")
    parser.add_argument("logs_dir")
    args = parser.parse_args()
    sort_experiment(Path(args.exp_dir), Path(args.logs_dir))
