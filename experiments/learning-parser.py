#! /usr/bin/env python

from pathlib import Path
import re
import sys

from lab.parser import Parser
from lab import tools

DK_REGEX = r"dk\.[0-9]+"


def parse_dk_files(content, props):
    all_files_with_dk_prefix = [str(x) for x in tools.natural_sort(Path(".").glob("dk*"))]
    numbered_dk_files = [x for x in all_files_with_dk_prefix if re.match(DK_REGEX, x)]

    if all_files_with_dk_prefix == ["dk"]:
        dk_file = "dk"
    elif len(numbered_dk_files) != len(all_files_with_dk_prefix):
        print(
            f"Error: the following files don't match the {DK_REGEX} regex:"
            f" {set(all_files_with_dk_prefix) - set(numbered_dk_files)}", file=sys.stderr)
        dk_file = None
    elif numbered_dk_files:
        dk_file = tools.natural_sort(numbered_dk_files)[-1]
    else:
        dk_file = None

    props["all_files_with_dk_prefix"] = all_files_with_dk_prefix
    props["dk_file"] = dk_file
    props["coverage"] = int(dk_file is not None)


def main():
    print("Running learning parser")
    parser = Parser()
    parser.add_function(parse_dk_files)
    parser.parse()


if __name__ == "__main__":
    main()
