#!/usr/bin/env python3

import sys

from lab.environments import TetralithEnvironment, LocalEnvironment

sys.path.insert(0, "..")
import project
import submissions
import tracks

import benchmarks
import planning_experiment

TRACK = tracks.SINGLE_CORE
TIME_LIMIT = 1800  # seconds
MEMORY_LIMIT = 8 * 1024  # MiB

if project.running_on_cluster():
    TESTRUN = False
    ENVIRONMENT = TetralithEnvironment(
        email="jendrik.seipp@liu.se",
        memory_per_cpu="9G",
        cpus_per_task=1,
        time_limit_per_task="23:00:00",
        export=["PATH"],
    )
else:
    TESTRUN = True
    ENVIRONMENT = LocalEnvironment(processes=4)
    TIME_LIMIT = 5  # seconds

exp = planning_experiment.PlanningExperiment(track=TRACK, time_limit=TIME_LIMIT, memory_limit=MEMORY_LIMIT, environment=ENVIRONMENT)
exp.add_planners(submissions.get_all_learners())
for domain, domain_dir in benchmarks.get_benchmarks(TESTRUN):
    exp.add_domain(domain, domain_dir)

project.add_collect_logs_step(exp)
exp.add_parse_again_step()
exp.run_steps()
