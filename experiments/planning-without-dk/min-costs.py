#! /usr/bin/env python

import json
from pathlib import Path
import sys

from downward.reports import PlanningReport

from lab.experiment import Experiment

sys.path.insert(0, "..")
import project


exp = Experiment()
exp.add_step(
    "remove-combined-properties", project.remove_file, Path(exp.eval_dir) / "properties"
)

project.fetch_algorithms(exp, "2023-07-02-planning-without-dk")
project.fetch_algorithm(exp, "2023-07-03-plan-costs", "lama", new_algo="lama-8h-32G")

class MinCostsReport(PlanningReport):
    """Write a JSON file mapping tasks to minimal plan costs."""
    def __init__(self, **kwargs):
        kwargs.setdefault('format', 'py')
        PlanningReport.__init__(self, **kwargs)

    def get_text(self):
        cost_map = {}
        for (domain, problem), runs in sorted(self.problem_runs.items()):
            costs = [run["cost"] for run in runs if run.get("cost") is not None]
            print(domain, problem, costs)
            min_cost = min(costs) if costs else None
            task = f"{domain}/testing/{problem.replace('-', '/')}"
            cost_map[task] = min_cost
        return json.dumps(cost_map, indent=2, sort_keys=True)

exp.add_report(MinCostsReport(), outfile="upper_bounds.json")

exp.run_steps()
