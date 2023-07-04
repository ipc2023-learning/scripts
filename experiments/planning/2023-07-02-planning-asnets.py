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
TESTRUN = False
ONE_TASK_PER_DOMAIN = False

NAMES = [
    "asnets.plan.sif",
]
PLANNERS = [submissions.IPCPlanner(submissions.IMAGES_DIR / name) for name in NAMES]

if project.running_on_cluster():
    ENVIRONMENT = TetralithEnvironment(
        email="jendrik.seipp@liu.se",
        memory_per_cpu="9G",
        cpus_per_task=1,
        time_limit_per_task="23:00:00",
        export=["PATH"],
        extra_options="#SBATCH --account=naiss2023-5-236",
    )
else:
    ENVIRONMENT = LocalEnvironment(processes=8)
    TIME_LIMIT = 180  # seconds
    ONE_TASK_PER_DOMAIN = True

exp = planning_experiment.PlanningExperiment(track=TRACK, logs_dir=LOGS_DIR, time_limit=TIME_LIMIT, memory_limit=MEMORY_LIMIT, environment=ENVIRONMENT)
exp.add_planners(PLANNERS)
for domain, domain_dir in benchmarks.get_planning_benchmarks(TESTRUN, one_task_per_domain=ONE_TASK_PER_DOMAIN):
    exp.add_domain(domain, domain_dir)

exp.add_parse_again_step()
exp.run_steps()
