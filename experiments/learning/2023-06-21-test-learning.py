#!/usr/bin/env python3

from lab.environments import TetralithEnvironment, LocalEnvironment

import benchmarks
import learning_experiment
import planners
import project
import tracks

TRACK = tracks.SINGLE_CORE
TIME_LIMIT = 24 * 60 * 60  # seconds
MEMORY_LIMIT = 32 * 1024  # MiB

if project.running_on_cluster():
    TESTRUN = False
    ENVIRONMENT = TetralithEnvironment(
        email="jendrik.seipp@liu.se",
        memory_per_cpu="33G",
        cpus_per_task=1,
        # 10 planners * 10 domains = 100 runs, so only one run per Slurm task --> use 1 day and 5 hours.
        time_limit_per_task="1-5",
        export=["PATH"],
    )
else:
    TESTRUN = True
    ENVIRONMENT = LocalEnvironment(processes=2)
    TIME_LIMIT = 10  # seconds
    MEMORY_LIMIT = 16 * 1024  # MiB

exp = learning_experiment.LearningExperiment(track=TRACK, time_limit=TIME_LIMIT, memory_limit=MEMORY_LIMIT, environment=ENVIRONMENT)
exp.add_planners(planners.get_all_learners())
for domain, domain_dir in benchmarks.get_benchmarks(TESTRUN):
    exp.add_domain(domain, domain_dir)

project.add_collect_logs_step(exp)
exp.add_parse_again_step()
exp.run_steps()
