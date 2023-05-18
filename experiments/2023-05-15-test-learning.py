#!/usr/bin/env python3

from lab.environments import TetralithEnvironment, LocalEnvironment

import benchmarks
import learning_experiment
import planners
import report
import tracks

TRACK = tracks.SINGLE_CORE
TIME_LIMIT = 1800  # seconds
MEMORY_LIMIT = 90 * 1024  # MiB

if learning_experiment.running_on_cluster():
    TESTRUN = False
    ENVIRONMENT = TetralithEnvironment(
        partition="infai_3",
        email="jendrik.seipp@liu.se",
        memory_per_cpu="91G",
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

exp.add_report(report.IPCPlanningReport(attributes=report.IPCPlanningReport.DEFAULT_ATTRIBUTES), outfile=f"{exp.name}.html")
exp.add_parse_again_step()
exp.run_steps()
