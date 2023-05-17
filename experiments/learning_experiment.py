import logging
from pathlib import Path
import sys

from downward import suites
from lab.experiment import Experiment, Run

from project import DIR, running_on_cluster


class LearningRun(Run):
    def __init__(self, experiment, planner, tasks, time_limit, memory_limit):
        super().__init__(experiment)
        domain = tasks[0].domain
        self.add_resource("domain", tasks[0].domain_file, "domain.pddl")
        task_names = []
        for task in tasks:
            task_name = Path(task.problem).stem
            task_names.append(task_name)
            self.add_resource(task_name, task.problem_file)
        self.add_command(
            "run-apptainer",
            [
                "{run_apptainer}",
                f"{{{planner.shortname}}}",
                time_limit,
                memory_limit,
                "dk",
                "{domain}",
            ] + [f"{{{task_name}}}" for task_name in task_names]
        )
        self.add_command("filter-stderr", [sys.executable, "{filter_stderr}"])

        self.set_property("algorithm", planner.shortname)
        self.set_property("planner_path", str(planner.image_path))
        self.set_property("domain", domain)
        self.set_property("problems", ", ".join(task.problem for task in tasks))
        self.set_property("id", [planner.shortname, domain])
        self.set_property("experiment_name", self.experiment.name)
        self.set_property("track", experiment.track)
        self.set_property("time_limit", time_limit)
        self.set_property("memory_limit", memory_limit)


class LearningExperiment(Experiment):
    def __init__(self, track, time_limit, memory_limit, path=None, environment=None):
        super().__init__(path=path, environment=environment)
        self._tasks = {}
        self._planners = {}
        self.track = track
        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.add_step("build", self.build)
        self.add_step("start", self.start_runs)
        self.add_fetcher(name="fetch")
        self.add_parser(DIR / "learning-parser.py")
        self.add_parser(DIR / "runsolver-parser.py")
        self.add_resource("run_apptainer", DIR / "run-apptainer.sh")
        self.add_resource("filter_stderr", DIR / "filter-stderr.py")

    def add_domain(self, domain, domain_dir):
        if domain in self._tasks:
            logging.critical(f"Domain {domain} was already added")
        domain_file = domain_dir / "domain.pddl"
        tasks = []
        for problem_file in sorted(domain_dir.glob("*.pddl")):
            if problem_file.name == "domain.pddl":
                continue
            tasks.append(suites.Problem(domain, problem_file.name, problem_file, domain_file))
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
                self.add_run(LearningRun(self, planner, tasks, self.time_limit, self.memory_limit))

        super().build(**kwargs)
