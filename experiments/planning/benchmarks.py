from pathlib import Path

DIR = Path(__file__).resolve().parent
REPO = DIR.parent
BENCHMARK_DIR = REPO / "../example-tasks/"


def get_benchmarks(test_run):
    benchmarks = [
        ("gripper", BENCHMARK_DIR / "gripper/training/easy"),
    ]
    if not test_run:
        benchmarks.extend([
        ("visitall", BENCHMARK_DIR / "visitall/training/easy"),
    ])
    return benchmarks


BEST_KNOWN_BOUNDS = {
    "gripper": {
        "p01.pddl": (None, None),
    },
}

def get_best_bounds(domain, problem):
    return BEST_KNOWN_BOUNDS.get(domain, {}).get(problem, (0, float("inf")))
