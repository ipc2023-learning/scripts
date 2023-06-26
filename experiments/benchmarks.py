from pathlib import Path

from downward import suites

DIR = Path(__file__).resolve().parent
REPO = DIR.parent
EXAMPLE_BENCHMARK_DIR = REPO / "../example-tasks/"
BENCHMARK_DIR = REPO / "../benchmarks/"

DOMAINS = [
    "blocksworld",
    "childsnack",
    "ferry",
    "floortile",
    "miconic",
    "rovers",
    "satellite",
    #"sokoban",
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


def get_planning_benchmarks(test_run):
    benchmarks = []
    for domain in ["gripper", "visitall"]:
        tasks = []
        for level in ["easy", "medium", "hard"]:
            tasks_dir = EXAMPLE_BENCHMARK_DIR / domain / "testing" / level
            domain_file = tasks_dir / "domain.pddl"
            for problem_file in sorted(tasks_dir.glob("*.pddl")):
                if problem_file.name == "domain.pddl":
                    continue
                tasks.append(suites.Problem(domain, f"{level}-{problem_file.name}", problem_file, domain_file))
        if test_run:
            tasks = tasks[:1]
        benchmarks.append((domain, tasks))
    return benchmarks


BEST_KNOWN_BOUNDS = {
    "gripper": {
        "p01.pddl": (None, None),
    },
}

def get_best_bounds(domain, problem):
    return BEST_KNOWN_BOUNDS.get(domain, {}).get(problem, (0, float("inf")))
