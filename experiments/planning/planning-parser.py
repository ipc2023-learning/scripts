#! /usr/bin/env python

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
    props["costs"] = []
    for plan in Path(".").glob("sas_plan*"):
        props["costs"].append(validate_plan("domain.pddl", "problem.pddl", str(plan)))

    props["has_invalid_plans"] = int(INVALID_PLAN in props["costs"])
    props["coverage"] = int(len(props["costs"]) > 0 and not props["has_invalid_plans"])
    if props["coverage"]:
        props["cost"] = min(props["costs"])


def main():
    print("Running planning parser")
    parser = Parser()
    parser.add_function(parse_plans)
    parser.parse()


if __name__ == "__main__":
    main()
