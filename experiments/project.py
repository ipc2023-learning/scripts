from pathlib import Path
import platform
import re
import subprocess
import sys

from downward.reports.absolute import AbsoluteReport
from downward.reports.scatter import ScatterPlotReport
from lab import tools
from lab.environments import BaselSlurmEnvironment, LocalEnvironment
from lab.experiment import ARGPARSER


# Silence import-unused messages. Experiment scripts may use these imports.
assert BaselSlurmEnvironment and LocalEnvironment and ScatterPlotReport


DIR = Path(__file__).resolve().parent
REPO = DIR.parent


def parse_args():
    ARGPARSER.add_argument("--tex", action="store_true", help="produce LaTeX output")
    ARGPARSER.add_argument(
        "--relative", action="store_true", help="make relative scatter plots"
    )
    return ARGPARSER.parse_args()


ARGS = parse_args()
TEX = ARGS.tex
RELATIVE = ARGS.relative


def running_on_cluster():
    node = platform.node()
    return node.endswith((".scicore.unibas.ch", ".cluster.bc2.ch")) or re.match(
        r"tetralith\d+\.nsc\.liu\.se|n\d+", node
    )


def get_repo_base() -> Path:
    """Get base directory of the repository, as an absolute path.

    Search upwards in the directory tree from the main script until a
    directory with a subdirectory named ".git" is found.

    Abort if the repo base cannot be found."""
    path = Path(tools.get_script_path())
    while path.parent != path:
        if (path / ".git").is_dir():
            return path
        path = path.parent
    sys.exit("repo base could not be found")


def remove_file(path: Path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def remove_properties(eval_dir: Path):
    for name in ["properties", "properties.xz"]:
        try:
            (eval_dir / name).unlink()
        except FileNotFoundError:
            pass


def _get_exp_dir_relative_to_repo():
    repo_name = get_repo_base().name
    script = Path(tools.get_script_path())
    script_dir = script.parent
    rel_script_dir = script_dir.relative_to(get_repo_base())
    expname = script.stem
    return repo_name / rel_script_dir / "data" / expname


def add_scp_step(exp, login, repos_dir):
    remote_exp = Path(repos_dir) / _get_exp_dir_relative_to_repo()
    exp.add_step(
        "scp-eval-dir",
        subprocess.call,
        [
            "scp",
            "-r",  # Copy recursively.
            "-C",  # Compress files.
            f"{login}:{remote_exp}-eval",
            f"{exp.path}-eval",
        ],
    )


def add_collect_logs_step(exp):
    exp.add_step("collect-logs", subprocess.check_call, ["./sort-logs.py", exp.path, DIR / "../../logs/"])


def fetch_algorithm(exp, expname, algo, *, new_algo=None):
    """Fetch (and possibly rename) a single algorithm from *expname*."""
    new_algo = new_algo or algo

    def rename_and_filter(run):
        if run["algorithm"] == algo:
            run["algorithm"] = new_algo
            run["id"][0] = new_algo
            return run
        return False

    exp.add_fetcher(
        f"data/{expname}-eval",
        filter=rename_and_filter,
        name=f"fetch-{new_algo}-from-{expname}",
        merge=True,
    )


def fetch_algorithms(exp, expname, *, algos=None, name=None, filters=None):
    """
    Fetch multiple or all algorithms.
    """
    assert not expname.rstrip("/").endswith("-eval")
    algos = set(algos or [])
    filters = filters or []
    if algos:

        def algo_filter(run):
            return run["algorithm"] in algos

        filters.append(algo_filter)

    exp.add_fetcher(
        f"data/{expname}-eval",
        filter=filters,
        name=name or f"fetch-from-{expname}",
        merge=True,
    )


def add_absolute_report(exp, *, name=None, outfile=None, **kwargs):
    report = AbsoluteReport(**kwargs)
    if name and not outfile:
        outfile = f"{name}.{report.output_format}"
    elif outfile and not name:
        name = Path(outfile).name
    elif not name and not outfile:
        name = f"{exp.name}-abs"
        outfile = f"{name}.{report.output_format}"

    if not Path(outfile).is_absolute():
        outfile = Path(exp.eval_dir) / outfile

    exp.add_report(report, name=name, outfile=outfile)
    exp.add_step(f"open-{name}", subprocess.call, ["xdg-open", outfile])
    #exp.add_step(f"publish-{name}", subprocess.call, ["publish", outfile])


def add_scatter_plot_reports(exp, algorithm_pairs, attributes, *, filter=None):
    for algo1, algo2 in algorithm_pairs:
        for attribute in attributes:
            exp.add_report(ScatterPlotReport(
                    relative=RELATIVE,
                    get_category=None if TEX else lambda run1, run2: run1["domain"],
                    attributes=[attribute],
                    filter_algorithm=[algo1, algo2],
                    filter=tools.make_list(filter),
                    format="tex" if TEX else "png",
                ),
                name=f"{exp.name}-{algo1}-{algo2}-{attribute}{'-relative' if RELATIVE else ''}")
