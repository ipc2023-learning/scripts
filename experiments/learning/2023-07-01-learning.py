#!/usr/bin/env python3

import sys

from lab.environments import TetralithEnvironment, LocalEnvironment

sys.path.insert(0, "..")
import benchmarks
import project
import submissions
import tracks

import learning_experiment

TRACK = tracks.SINGLE_CORE
TIME_LIMIT = 24 * 60 * 60  # seconds
MEMORY_LIMIT = 32 * 1024  # MiB
TESTRUN = False

if project.running_on_cluster():
    ENVIRONMENT = TetralithEnvironment(
        email="jendrik.seipp@liu.se",
        memory_per_cpu="33G",
        cpus_per_task=1,
        # 10 planners * 10 domains = 100 runs, so only one run per Slurm task --> use 1 day and 5 hours.
        time_limit_per_task="1-5",
        export=["PATH"],
        extra_options="#SBATCH --account=naiss2023-5-236",
    )
else:
    ENVIRONMENT = LocalEnvironment(processes=8)
    TIME_LIMIT = 2  # seconds
    MEMORY_LIMIT = 16 * 1024  # MiB

exp = learning_experiment.LearningExperiment(track=TRACK, time_limit=TIME_LIMIT, memory_limit=MEMORY_LIMIT, environment=ENVIRONMENT)
exp.add_planners(submissions.get_all_learners())
for domain_name, domain_file, domain_dir in benchmarks.get_learning_benchmarks(TESTRUN):
    exp.add_domain(domain_name, domain_file, domain_dir)

project.add_collect_logs_step(exp)
exp.add_parse_again_step()
exp.run_steps()
