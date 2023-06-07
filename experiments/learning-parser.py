#! /usr/bin/env python

from pathlib import Path

from lab.parser import Parser
from lab import tools


def parse_dk_files(content, props):
    props["all_files"] = tools.natural_sort(Path(".").iterdir())
    props["dk_files"] = tools.natural_sort(Path(".").glob("dk.[0-9]*"))
    props["coverage"] = int(len(props["dk_files"]) > 0)
    if props["dk_files"]:
        props["dk_file"] = props["dk_files"][-1]


def main():
    print("Running learning parser")
    parser = Parser()
    parser.add_function(parse_dk_files)
    parser.parse()


if __name__ == "__main__":
    main()
