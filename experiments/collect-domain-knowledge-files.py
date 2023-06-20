#!/usr/bin/env python3

import argparse
from pathlib import Path
import shutil

from lab.tools import Properties


def fetch_dk_file(run_dir, dk_dir):
    print(f"Searching for domain knowledge file in {run_dir}")
    props = Properties(str(run_dir / "static-properties"))
    algorithm = props["algorithm"]
    domain = props["domain"]
    experiment = props["experiment_name"]
    dk_file = props.get("dk_file")
    if dk_file is None:
        return
    source = run_dir / dk_file
    target = dk_dir / experiment / algorithm / f"{domain}.dk"
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Copy {source} to {target}")
    shutil.copy2(source, target)


def collect_dk_files(exp_dir, dk_dir):
    for run_dir in sorted(exp_dir.glob("runs-*/*")):
        fetch_dk_file(run_dir, dk_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_dir")
    parser.add_argument("domain_knowledge_dir")
    args = parser.parse_args()
    collect_dk_files(Path(args.exp_dir), Path(args.domain_knowledge_dir))
