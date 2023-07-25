#!/usr/bin/env python3

import argparse
import io
import os
from pathlib import Path
import shutil
import tarfile

from lab.tools import Properties

MAX_FILE_SIZE = 10 * 1024  # Bytes
PART_SIZE = MAX_FILE_SIZE // 2


def tar_add_large_files(tar, filepath, arcname):
    filesize = filepath.stat().st_size
    if filesize > MAX_FILE_SIZE:
        print(f"File too large: {filepath}")
        with open(filepath, 'rb') as f:
            first_part = f.read(PART_SIZE)
            f.seek(-PART_SIZE, os.SEEK_END)
            last_part = f.read(PART_SIZE)
        buffer = first_part + b"\n\n\n\n\n ===== FILE TOO LARGE --> MIDDLE FILE CONTENTS OMITTED ===== \n\n\n\n\n" +  last_part
        fileobj = io.BytesIO(buffer)
        file_obj = tarfile.TarInfo(name=arcname)
        file_obj.size = len(buffer)
        tar.addfile(file_obj, fileobj=fileobj)
    else:
        tar.add(filepath, arcname=arcname)


def sort_run_dir(run_dir, logs_dir):
    print(f"Fetching data from {run_dir}")
    props = Properties(str(run_dir / "static-properties"))
    dynamic_props = Properties(str(run_dir / "properties"))
    props.update(dynamic_props)
    algorithm = props["algorithm"]
    experiment = props["experiment_name"]
    target_root_dir = logs_dir / f"{algorithm}" / experiment
    target_dk_dir = target_root_dir / "domain-knowledge"
    target_run_dir = target_root_dir / run_dir.parent.name / run_dir.name
    target_run_dir.mkdir(parents=True, exist_ok=True)
    uncompressed_files = {"properties", "static-properties", "driver.log", "run", "values.log"}
    compressed_files = []

    for root, _, files in os.walk(run_dir):
        for file in files:
            filepath = Path(root) / file
            if filepath.name not in uncompressed_files:
                compressed_files.append(filepath)

    tar_filename = target_run_dir / "other_files.tgz"

    with tarfile.open(tar_filename, 'w:gz') as tar:
        for f in compressed_files:
            rel_path = os.path.relpath(f, run_dir)
            arcname = f"{rel_path}"
            tar_add_large_files(tar, f, arcname)

    for path in uncompressed_files:
        if (run_dir / path).exists():
            shutil.copy2(run_dir / path, target_run_dir)

    # Collect domain knowledge file.
    dk_file = props.get("dk_file")
    if dk_file is None:
        return
    source = run_dir / dk_file
    domain = props["domain"]
    target = target_dk_dir / f"{domain}.dk"
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Copy {source} to {target}")
    shutil.copy2(source, target)


def sort_experiment(exp_dir, logs_dir):
    for run_dir in sorted(exp_dir.glob("runs-*/*")):
        sort_run_dir(run_dir, logs_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_dir")
    parser.add_argument("logs_dir")
    args = parser.parse_args()
    sort_experiment(Path(args.exp_dir), Path(args.logs_dir))
