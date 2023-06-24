import logging
import math
from pathlib import Path
import shutil
import subprocess

from downward.reports.absolute import AbsoluteReport
from downward import suites
from lab.experiment import Experiment, Run
from lab import tools

import project

DIR = project.DIR / "planning"


class PlanningRun(Run):
    def __init__(self, experiment, planner, dk_file, task, time_limit, memory_limit):
        super().__init__(experiment)
        self.add_resource(
            "domain_knowledge", dk_file, "dk", symlink=False
        )
        self.add_resource(
            "domain", task.domain_file, "domain.pddl", symlink=False
        )
        self.add_resource(
            "problem", task.problem_file, "problem.pddl", symlink=False
        )
        self.add_command(
            "run-apptainer",
            [
                "{run_apptainer}",
                f"{{{planner.shortname}}}",
                "{domain_knowledge}",
                "{domain}",
                "{problem}",
                "sas_plan",
                time_limit,
                memory_limit
            ]
        )

        self.set_property("algorithm", planner.shortname)
        self.set_property("planner_path", str(planner.image_path))
        self.set_property("domain", str(task.domain))
        self.set_property("problem", str(task.problem))
        self.set_property("id", [planner.shortname, str(task.domain), str(task.problem)])
        self.set_property("experiment_name", self.experiment.name)
        self.set_property("track", experiment.track)
        self.set_property("time_limit", time_limit)
        self.set_property("memory_limit", memory_limit)


class PlanningExperiment(Experiment):
    def __init__(self, track, logs_dir, time_limit, memory_limit, path=None, environment=None):
        super().__init__(path=path, environment=environment)
        self._tasks = {}
        self._planners = {}
        self.track = track
        self.logs_dir = logs_dir
        self.learning_exp_name = self.name.replace("planning", "learning")
        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.add_step("build", self.build)
        self.add_step("start", self.start_runs)
        self.add_fetcher(name="fetch")
        if not project.running_on_cluster():
            self.add_step("remove-eval-dir", shutil.rmtree, self.eval_dir, ignore_errors=True)
            project.add_scp_step(self, "nsc", "/proj/dfsplan/users/x_jense/ipc2023-learning")
        reportfile = Path(self.eval_dir) / f"{self.name}.html"
        self.add_report(IPCPlanningReport(attributes=IPCPlanningReport.DEFAULT_ATTRIBUTES), outfile=reportfile)
        if not project.running_on_cluster():
            self.add_step(f"open-{reportfile.name}", subprocess.call, ["xdg-open", reportfile])

        self.add_parser(DIR / "planning-parser.py")
        self.add_parser(project.DIR / "runsolver-parser.py")
        self.add_resource("run_apptainer", DIR / "run-apptainer.sh")

    def add_domain(self, domain, tasks):
        if domain in self._tasks:
            logging.critical(f"Domain {domain} was already added")
        self._tasks[domain] = tasks

    def add_planners(self, planners):
        for planner in planners:
            self.add_planner(planner)

    def add_planner(self, planner):
        if planner.shortname in self._planners:
            logging.critical(f"Planner with name '{planner.shortname}' added twice.")
        self.add_resource(planner.shortname, planner.image_path, symlink=True)
        self._planners[planner.shortname] = planner

    def build(self, **kwargs):
        if not self._planners:
            logging.critical("You must add at least one planner image.")

        # Convert suite to strings (see FastDownwardExperiment.build).
        serialized_suites = {
            str(domain): [str(task) for task in tasks]
            for domain, tasks in self._tasks.items()
        }
        self.set_property("suite", serialized_suites)
        self.set_property("images", list(self._planners.keys()))

        for planner in self._planners.values():
            for domain, tasks in sorted(self._tasks.items()):
                dk_file = (self.logs_dir / planner.shortname.replace("_plan", "_learn") / self.learning_exp_name / "domain-knowledge" / f"{domain}.dk").resolve()
                if not dk_file.is_file():
                    print(f"DK file missing: {dk_file}")
                    continue
                for task in tasks:
                    self.add_run(PlanningRun(self, planner, dk_file, task, self.time_limit, self.memory_limit))

        super().build(**kwargs)


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
    ERROR_ATTRIBUTES = [
        "domain",
        "problem",
        "algorithm",
        "unexplained_errors",
        "error",
        "cpu_time",
        "wall_clock_time",
        "virtual_memory",
        "memory",
        "node",
    ]
    INFO_ATTRIBUTES = []
    def __init__(self, **kwargs):
        filters = tools.make_list(kwargs.get("filter", []))
        #filters.append(add_score)
        kwargs["filter"] = filters
        super().__init__(**kwargs)
