#!/usr/bin/env python3

import sys

from lab.environments import TetralithEnvironment, LocalEnvironment

sys.path.insert(0, "..")
import benchmarks
import project
import submissions
import tracks

import planning_experiment

TRACK = tracks.SINGLE_CORE
LOGS_DIR = project.REPO / ".." / "logs"
TIME_LIMIT = 1800  # seconds
MEMORY_LIMIT = 8 * 1024  # MiB
TESTRUN = True

if project.running_on_cluster():
    ENVIRONMENT = TetralithEnvironment(
        email="jendrik.seipp@liu.se",
        memory_per_cpu="9G",
        cpus_per_task=1,
        time_limit_per_task="23:00:00",
        export=["PATH"],
    )
else:
    ENVIRONMENT = LocalEnvironment(processes=4)
    TIME_LIMIT = 5  # seconds

exp = planning_experiment.PlanningExperiment(track=TRACK, logs_dir=LOGS_DIR, time_limit=TIME_LIMIT, memory_limit=MEMORY_LIMIT, environment=ENVIRONMENT)
exp.add_planners(submissions.get_all_planners())
for domain, domain_dir in benchmarks.get_planning_benchmarks(TESTRUN):
    exp.add_domain(domain, domain_dir)

exp.add_parse_again_step()
exp.run_steps()
