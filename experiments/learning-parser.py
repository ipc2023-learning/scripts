#! /usr/bin/env python

from pathlib import Path

from lab.parser import Parser
from lab import tools


def parse_dk_files(content, props):
    props["dk_files"] = tools.natural_sort(Path(".").glob("dk*"))
    props["coverage"] = int(len(props["dk_files"]) > 0)


def main():
    print("Running learning parser")
    parser = Parser()
    parser.add_function(parse_dk_files)
    parser.parse()


if __name__ == "__main__":
    main()
