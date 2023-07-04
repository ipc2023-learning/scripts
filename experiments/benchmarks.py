import json
from pathlib import Path

from downward import suites

DIR = Path(__file__).resolve().parent
REPO = DIR.parent
EXAMPLE_BENCHMARK_DIR = REPO / "../example-tasks/"
BENCHMARK_DIR = REPO / "../benchmarks/"
BOUNDS_DIR = BENCHMARK_DIR / "solutions"

DOMAINS = [
    "blocksworld",
    "childsnack",
    "ferry",
    "floortile",
    "miconic",
    "rovers",
    "satellite",
    "sokoban",
    "spanner",
    "transport",
]


def get_learning_benchmarks(test_run):
    if test_run:
        return [
            ("gripper", EXAMPLE_BENCHMARK_DIR / "gripper/training/easy/domain.pddl", EXAMPLE_BENCHMARK_DIR / "gripper/training/easy"),
            ("visitall", EXAMPLE_BENCHMARK_DIR / "visitall/training/easy/domain.pddl", EXAMPLE_BENCHMARK_DIR / "visitall/training/easy"),
        ]
    else:
        return [
            (domain, BENCHMARK_DIR / domain / "domain.pddl", BENCHMARK_DIR / f"{domain}/training/easy")
            for domain in DOMAINS
        ]


def get_planning_benchmarks(test_run, one_task_per_domain=False):
    benchmarks = []
    if test_run:
        for domain in ["gripper", "visitall"]:
            tasks = []
            for level in ["easy", "medium", "hard"]:
                tasks_dir = EXAMPLE_BENCHMARK_DIR / domain / "testing" / level
                domain_file = tasks_dir / "domain.pddl"
                for problem_file in sorted(tasks_dir.glob("*.pddl")):
                    if problem_file.name == "domain.pddl":
                        continue
                    tasks.append(suites.Problem(domain, f"{level}-{problem_file.name}", problem_file, domain_file))
            #if test_run:
            #    tasks = tasks[:1]
            benchmarks.append((domain, tasks))
    else:
        for domain in DOMAINS:
            tasks = []
            for level in ["easy", "medium", "hard"]:
                tasks_dir = BENCHMARK_DIR / domain / "testing" / level
                domain_file = BENCHMARK_DIR / domain / "domain.pddl"
                for problem_file in sorted(tasks_dir.glob("p??.pddl")):
                    tasks.append(suites.Problem(domain, f"{level}-{problem_file.name}", problem_file, domain_file))
            if one_task_per_domain:
                tasks = tasks[:1]
            benchmarks.append((domain, tasks))
    return benchmarks


BEST_KNOWN_UPPER_BOUNDS = {}
for filename in ["upper_bounds.json", "upper_bounds_from_ipc_planners.json"]:
    with open(BOUNDS_DIR / filename) as f:
        bounds = json.load(f)
        # Use minimum upper bound over all files.
        for task, bound in sorted(bounds.items()):
            if task not in BEST_KNOWN_UPPER_BOUNDS or (bound is not None and bound < BEST_KNOWN_UPPER_BOUNDS[task]):
                BEST_KNOWN_UPPER_BOUNDS[task] = bound


def get_best_upper_bound(domain, problem):
    task = f"{domain}/testing/{problem.replace('-', '/')}"
    return BEST_KNOWN_UPPER_BOUNDS[task]
