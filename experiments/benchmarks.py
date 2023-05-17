from pathlib import Path

DIR = Path(__file__).resolve().parent
REPO = DIR.parent
BENCHMARK_DIR = REPO / "../example-tasks/"


def get_benchmarks(test_run):
    # TODO: use correct domains for each track (use full domains normally and only one problem per domain if test_run is true).
    benchmarks = [
        ("gripper", BENCHMARK_DIR / "gripper/training/easy"),
        ("visitall", BENCHMARK_DIR / "visitall/training/easy"),
    ]
    return benchmarks


BEST_KNOWN_BOUNDS = {
    "gripper": {
        "p01.pddl": (None, None),
    },
}

def get_best_bounds(domain, problem):
    return BEST_KNOWN_BOUNDS.get(domain, {}).get(problem, (0, float("inf")))
