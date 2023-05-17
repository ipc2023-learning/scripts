#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil
from subprocess import check_call

from lab.tools import Properties


def sort_run_dir(run_dir, logs_dir):
    props = Properties(str(run_dir / "static-properties"))
    algorithm = props["algorithm"]
    experiment = props["experiment_name"]
    target = logs_dir/f"{algorithm}"/experiment/run_dir.parent.name/run_dir.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(run_dir, target)
    uncompressed_files = ["properties", "static-properties", "driver.log", "run.err", "run.log", "values.log", "watch.log"]
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_dir")
    parser.add_argument("logs_dir")
    args = parser.parse_args()
    sort_experiment(Path(args.exp_dir), Path(args.logs_dir))
