#! /usr/bin/env python

import sys

from lab.parser import Parser


def set_outcome(content, props):
    lines = content.splitlines()
    success = props["coverage"]
    out_of_time = int("TIMEOUT=true" in lines)
    out_of_memory = int("MEMOUT=true" in lines)
    # runsolver decides "out of time" based on CPU rather than (cumulated)
    # WCTIME.
    if (
        not success
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
    if success and (out_of_time or out_of_memory):
        print("output file found but runsolver recorded an out_of_*")
        print(props)
        out_of_time = 0
        out_of_memory = 0

    if success ^ out_of_time ^ out_of_memory:
        if success:
            props["error"] = "success"
        elif out_of_time:
            props["error"] = "out_of_time"
        elif out_of_memory:
            props["error"] = "out_of_memory"
    else:
        print(f"unexpected error: {props}", file=sys.stderr)
        props["error"] = "unexpected-error"


def main():
    print("Running runsolver parser")
    parser = Parser()
    parser.add_pattern(
        "node", r"node: (.+)\n", type=str, file="driver.log", required=True
    )
    parser.add_pattern(
        "apptainer_exit_code",
        r"run-apptainer exit code: (.+)\n",
        type=int,
        file="driver.log",
        required=True,
    )
    parser.add_pattern(
        "apptainer_wall_clock_time",
        r"run-apptainer wall-clock time: (.+)s",
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
    parser.add_function(set_outcome, file="values.log")
    parser.parse()


if __name__ == "__main__":
    main()
