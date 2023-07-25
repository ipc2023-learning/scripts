import logging
import math
from pathlib import Path
import shutil
import subprocess

from downward.reports.absolute import AbsoluteReport
from lab.experiment import Experiment, Run
from lab.reports import Attribute
from lab import tools

import benchmarks
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
            ],
            hard_stdout_limit=50 * 1024,  # KiB
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
        self.learning_exp_name = self.name.replace("planning", "learning").replace("-asnets", "").replace("-muninn-gpu", "")
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

        error_reportfile = Path(self.eval_dir) / f"{self.name}-errors.html"
        self.add_report(IPCPlanningReport(attributes=[Attribute("has_invalid_plans", absolute=True), "run_dir"]), outfile=error_reportfile)
        if not project.running_on_cluster():
            self.add_step(f"open-{error_reportfile.name}", subprocess.call, ["xdg-open", error_reportfile])

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

        logging.info(f"Planners: {len(self._planners)}")
        logging.info(f"Tasks: {[len(tasks) for domain, tasks in sorted(self._tasks.items())]}")
        for planner in self._planners.values():
            for domain, tasks in sorted(self._tasks.items()):
                dk_file = (self.logs_dir / planner.shortname.replace("_plan", "_learn") / self.learning_exp_name / "domain-knowledge" / f"{domain}.dk").resolve()
                if not dk_file.is_file():
                    print(f"DK file missing: {dk_file}")
                    continue
                for task in tasks:
                    self.add_run(PlanningRun(self, planner, dk_file, task, self.time_limit, self.memory_limit))

        super().build(**kwargs)


def add_scores(run):
    if run["coverage"]:
        best_upper_bound = benchmarks.get_best_upper_bound(run["domain"], run["problem"])
        run["quality_score"] = 1. if best_upper_bound is None else best_upper_bound / run["cost"]

        time_limit = run["time_limit"]
        time = run["time_for_first_plan"]
        run["agile_score"] = 1. if time <= 1 else 1 - (math.log(time) / math.log(time_limit))
    else:
        run["quality_score"] = 0.
        run["agile_score"] = 0.
    return run


class IPCPlanningReport(AbsoluteReport):
    DEFAULT_ATTRIBUTES = ["coverage", "cost", "costs", "apptainer_wall_clock_time",
                          "error", "run_dir", Attribute("has_invalid_plans", absolute=True),
                          "cpu_time", "memory", "virtual_memory", "wall_clock_time",
                          "time_for_first_plan", "plan_times", Attribute("agile_score", absolute=True, min_wins=False),
                          Attribute("quality_score", absolute=True, min_wins=False)]
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
        filters.append(add_scores)
        kwargs["filter"] = filters
        super().__init__(**kwargs)
