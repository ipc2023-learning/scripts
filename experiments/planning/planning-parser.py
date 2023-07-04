#! /usr/bin/env python

import datetime
from pathlib import Path
import subprocess
import sys

from lab.parser import Parser

INVALID_PLAN = "invalid"


def validate_plan(domain, problem, plan):
    try:
        validate_output = subprocess.check_output(
            ["validate", domain, problem, plan],
            stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        validate_output = e.output.decode()
    plan_valid = False
    plan_cost = None
    for line in validate_output.splitlines():
        if line.strip() == "Plan valid":
            plan_valid = True
        elif line.startswith("Value: "):
            plan_cost = int(line[len("Value: "):])
    if plan_valid:
        return plan_cost
    else:
        print(f"Invalid plan: {validate_output}", file=sys.stderr)
        return INVALID_PLAN


def parse_plans(content, props):
    # Convert start time with format "2023-07-04T11:41:14.942" to datetime object.
    start_time = datetime.datetime.strptime(props["start_time"], "%Y-%m-%dT%H:%M:%S.%f")
    print(f"Start time: {start_time}")
    props["costs"] = []
    props["plan_times"] = []
    for plan in sorted(Path(".").glob("sas_plan*")):
        ctime = datetime.datetime.fromtimestamp(plan.stat().st_ctime)
        plan_time = ctime - start_time
        props["costs"].append(validate_plan("domain.pddl", "problem.pddl", str(plan)))
        props["plan_times"].append(round(plan_time.total_seconds(), 2))

    props["has_invalid_plans"] = int(INVALID_PLAN in props["costs"])
    props["coverage"] = int(len(props["costs"]) > 0 and not props["has_invalid_plans"])
    if props["coverage"]:
        props["cost"] = min(props["costs"])
        props["time_for_first_plan"] = min(props["plan_times"])


def main():
    print("Running planning parser")
    parser = Parser()
    parser.add_pattern(
        "start_time",
        r"Start time: (.+)\n",
        type=str,
        required=True,
    )
    parser.add_function(parse_plans)
    parser.parse()


if __name__ == "__main__":
    main()
