#! /usr/bin/env python

from pathlib import Path
from subprocess import check_output, CalledProcessError
import sys

from lab.parser import Parser

INVALID_PLAN = "invalid"

def validate_plan(domain, problem, plan):
    try:
        validate_output = check_output(["validate", domain, problem, plan]).decode()
    except CalledProcessError as e:
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
        return INVALID_PLAN

def parse_plans(content, props):
    props["costs"] = []
    for plan in Path(".").glob("sas_plan*"):
        props["costs"].append(validate_plan("domain.pddl", "problem.pddl", str(plan)))

    props["has_invalid_plans"] = int(INVALID_PLAN in props["costs"])
    props["coverage"] = int(len(props["costs"]) > 0 and not props["has_invalid_plans"])
    if props["coverage"]:
        props["cost"] = min(props["costs"])


def set_outcome(content, props):
    lines = content.splitlines()
    solved = props["coverage"]
    out_of_time = int("TIMEOUT=true" in lines)
    out_of_memory = int("MEMOUT=true" in lines)
    # runsolver decides "out of time" based on CPU rather than (cumulated)
    # WCTIME.
    if (
        not solved
        and not out_of_time
        and not out_of_memory
        and props["total_wall_clock_time"] > props["time_limit"]
    ):
        out_of_time = 1
    # In cases where CPU time is very slightly above the threshold so that
    # runsolver didn't kill the planner yet and the planner solved a task
    # just within the limit, runsolver will still record an "out of time".
    # We remove this record. This case also applies to iterative planners.
    # If such planners solve the task, we don't treat them as running out
    # of time.
    if solved and (out_of_time or out_of_memory):
        print("task solved however runsolver recorded an out_of_*")
        print(props)
        out_of_time = 0
        out_of_memory = 0

    if solved ^ out_of_time ^ out_of_memory:
        if solved:
            props["error"] = "solved"
        elif out_of_time:
            props["error"] = "out_of_time"
        elif out_of_memory:
            props["error"] = "out_of_memory"
    else:
        print(f"unexpected error: {props}", file=sys.stderr)
        props["error"] = "unexpected-error"


def main():
    print("Running planning parser")
    parser = Parser()
    parser.add_pattern(
        "planner_exit_code",
        r"run-planner exit code: (.+)\n",
        type=int,
        file="driver.log",
        required=True,
    )
    parser.add_pattern(
        "node", r"node: (.+)\n", type=str, file="driver.log", required=True
    )
    parser.add_pattern(
        "planner_wall_clock_time",
        r"run-planner wall-clock time: (.+)s",
        type=float,
        file="driver.log",
        required=True,
    )
    parser.add_pattern(
        "time_limit",
        r"Enforcing CPUTime limit \(soft limit, will send "
        r"SIGTERM then SIGKILL\): (\d+) seconds",
        type=int,
        file="watch.log",
        required=True,
    )
    # Includes solver and all child processes.
    parser.add_pattern(
        "total_cpu_time", r"CPUTIME=(.+)", type=float, file="values.log", required=True
    )
    parser.add_pattern(
        "total_wall_clock_time", r"WCTIME=(.+)", type=float, file="values.log", required=True
    )
    parser.add_pattern(
        "total_virtual_memory", r"MAXVM=(\d+)", type=int, file="values.log", required=True
    )
    parser.add_function(parse_plans)
    parser.add_function(set_outcome, file="values.log")
    parser.parse()


if __name__ == "__main__":
    main()
