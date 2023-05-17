from collections import defaultdict, OrderedDict
import logging
from pathlib import Path

from downward import suites
from lab.experiment import Experiment, Run

DIR = Path(__file__).resolve().parent


class IPCRun(Run):
    def __init__(self, experiment, planner, task, time_limit, memory_limit):
        super().__init__(experiment)
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
    def __init__(self, track, time_limit, memory_limit, path=None, environment=None):
        super().__init__(path=path, environment=environment)
        self._suites = defaultdict(list)
        self._planners = OrderedDict()
        self.track = track
        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.add_step("build", self.build)
        self.add_step("start", self.start_runs)
        self.add_fetcher(name="fetch")
        self.add_parser(DIR / "planning-parser.py")
        self.add_resource("run_apptainer", DIR / "run-apptainer.sh")

    def _get_tasks(self):
        tasks = []
        for benchmarks_dir, suite in self._suites.items():
            tasks.extend(suites.build_suite(str(benchmarks_dir), suite))
        return tasks

    def add_suite(self, benchmarks_dir, suite):
        if isinstance(suite, str):
            suite = [suite]
        benchmarks_dir = Path(benchmarks_dir).resolve()
        if not benchmarks_dir.exists():
            logging.critical(f"Benchmarks directory {str(benchmarks_dir)} not found.")
        self._suites[benchmarks_dir].extend(suite)

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
            str(benchmarks_dir): [str(problem) for problem in benchmarks]
            for benchmarks_dir, benchmarks in self._suites.items()
        }
        self.set_property("suite", serialized_suites)
        self.set_property("images", list(self._planners.keys()))

        tasks = self._get_tasks()
        for planner in self._planners.values():
            for task in tasks:
                self.add_run(IPCRun(self, planner, task, self.time_limit, self.memory_limit))

        super().build(**kwargs)
