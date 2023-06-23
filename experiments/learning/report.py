#! /usr/bin/env python

import math

from downward.reports.absolute import AbsoluteReport
from lab.tools import make_list

import benchmarks
import tracks


def add_score(run):
    score = 0
    if "coverage" not in run:
        print(run)
    if run["coverage"]:
        track = run["track"]
        best_lower_bound, best_upper_bound = benchmarks.get_best_bounds(run["domain"], run["problem"])
        if track == tracks.OPT:
            assert len(run["costs"]) == 1 and run["costs"][0] == run["cost"]
            cost = run["cost"]
            if cost < best_lower_bound or cost > best_upper_bound:
                run["has_suboptimal_plan"] = 1
                score = 0
            else:
                run["has_suboptimal_plan"] = 0
                score = 1
        elif track == tracks.SAT:
            score = best_upper_bound / run["cost"]
        elif track == tracks.AGL:
            time_limit = run["time_limit"]
            time = run["cpu_time"]
            if time <= 1:
                score = 1
            else:
                score = 1 - math.log(time) / math.log(time_limit)
    run["score"] = score
    return run


class IPCPlanningReport(AbsoluteReport):
    DEFAULT_ATTRIBUTES = ["coverage", "cost", "costs", "planner_exit_code", "planner_wall_clock_time",
                          "score", "error", "run_dir", "has_suboptimal_plan", "has_invalid_plans",
                          "cpu_time", "virtual_memory", "wall_clock_time"]
    def __init__(self, **kwargs):
        filters = make_list(kwargs.get("filter", []))
        filters.append(add_score)
        kwargs["filter"] = filters
        super().__init__(**kwargs)


class IPCLearningReport(AbsoluteReport):
    DEFAULT_ATTRIBUTES = ["apptainer_exit_code", "apptainer_wall_clock_time",
                          "error", "run_dir", "cpu_time",
                          "virtual_memory", "memory", "wall_clock_time",
                          "coverage", "all_files_with_dk_prefix", "dk_file"]
    INFO_ATTRIBUTES = []
