#!/usr/bin/env python3
"""Figure 1 - composition of the MDArena dataset.

Two panels, both read from `[metadata]` in each task's `task.toml`:

    task type      pie, one value per task, sums to 50
    packages       bars, several values per task, does not sum to 50

The task selection and categories are checked against the manuscript's v0.2
and v1.0 task-summary CSVs. Historical v0.1 tasks are excluded from this check.
Package metadata still come from the benchmark
because the model-result tables do not contain that field.

The v1 figure was built from three CSVs in this repository that had no link to
the tasks and disagreed with them - the same task could be "Trajectory analysis"
in the figure and `structure_analysis` in `task.toml`. Those CSVs are abandoned;
`task.toml` is the single source of truth, and the benchmark's own validator
enforces the vocabularies, so this figure cannot drift from the dataset again.

Task type is a partition and therefore drawn as a pie; `packages` is multi-valued
and drawn as bars, so the different chart type signals that it does not sum to 50.

Usage:
    python make_figure_1.py                 # finds MDArena-dev alongside this repo
    MDARENA_REPO=/path/to/MDArena-dev python make_figure_1.py
"""

from __future__ import annotations

import collections
import csv
import math
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - the paper environment is 3.11+
    import tomli as tomllib


SCRIPT_DIR = Path(__file__).resolve().parent
CHAPTER = Path(__file__).resolve().parents[3]
HERE = CHAPTER / "figures/figure_1"
sys.path.insert(0, str(SCRIPT_DIR.parent))
from benchmark_versions import BENCHMARK_VERSIONS  # noqa: E402

DATA = CHAPTER / "data"
REPO_NAME = "MDArena-dev"
OUT_STEM = HERE / "figure_1"

# Dataset category palette. Categories arrive largest-first and take colours
# in this order.
CATEGORICAL = [
    "#90BE6D",
    "#43AA8B",
    "#F8961E",
    "#F3722C",
    "#F9C74F",
    "#F94144",
    "#577590",
]
FALLBACK_COLOUR = "#577590"
BAR_COLOUR = "#577590"

# Packages appearing on fewer than this many tasks are pooled into a single
# "Others" bar and named in the caption. Set to 1 to show every package.
MIN_PACKAGE_COUNT = 2

# Whether the pooled packages also get an "Others" bar. Off by default: every
# other bar means "tasks using this package", while an Others bar would mean
# "tasks using any of seven packages" - a different quantity on the same axis,
# which invites a reader to compare it against PLUMED or ParmEd as though it
# were one package.
POOL_OTHERS = False

TITLE_SIZE = 14

# Thickness of the panel B bars, as a fraction of the row spacing.
BAR_HEIGHT = 0.55

# Wedges narrower than this (per cent) get no inline label.
PCT_LABEL_MIN = 5.0

# Place the legend directly below the pie, relative to the axes' bottom edge.
LEGEND_TOP = 0.00

# Pie radius in axes units. Slightly over 1, which overflows the unit circle
# matplotlib fits to the axes; the room comes from the legend having moved up.
#
# This pair is bounded by the wedges colliding with the legend, not by taste.
# The gap between the lowest wedge and the top of the legend, as a fraction of
# figure height, goes 1.05/0.00 -> +0.070, 1.10/0.04 -> +0.029, 1.20/0.10 ->
# -0.039, and the last of those overlaps. Raise either value and re-measure
# rather than judging it by eye at display size - the collision is only obvious
# at full resolution.
PIE_RADIUS = 1.05

# Display names. The stored values are snake_case identifiers; these are what a
# reader should see. Any value missing here is title-cased as a fallback, which
# is visible enough to prompt adding it rather than silently looking fine.
LABELS = {
    "analysis": "Analysis",
    "system_preparation": "System preparation",
    "free_energy": "Free energy",
    "enhanced_sampling": "Enhanced sampling",
    "parameterization": "Parameterization",
    "diagnostics": "Diagnostics",
    "quantum_chemistry": "Quantum chemistry",
}


def label(value: str) -> str:
    return LABELS.get(value, value.replace("_", " ").capitalize())


def panel_label(ax, letter: str) -> None:
    """Place the panel letter at a fixed offset from the axes' top-left corner.

    The offset is in points so it stays consistent across axes of different widths.
    """
    ax.annotate(
        letter,
        xy=(0, 1),
        xycoords="axes fraction",
        xytext=(-22, 12),
        textcoords="offset points",
        fontsize=14,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def find_repo() -> Path | None:
    """Search this directory and every ancestor for a MDArena-dev checkout.

    This replaces a hard-coded HERE.parents[3], which assumed the script sits
    exactly three levels below the directory holding MDArena-dev. That holds in
    MDArena_paper (figures/v2/figure_1) and fails in MDArena_NeurIPS_2026
    (figures/figure_1), where it resolved one level too high and reported no
    tasks/ directory. Walking up instead works at any depth, and requiring
    tasks/ means a same-named directory that is not a checkout is skipped
    rather than accepted and then failing later.
    """
    local = DATA / "benchmark"
    if (local / "tasks").is_dir():
        return local
    for base in (HERE, *HERE.parents):
        candidate = base / REPO_NAME
        if (candidate / "tasks").is_dir():
            return candidate
    return None


def read_task_categories() -> dict[str, str]:
    """Use the current task selection, checked against the v0.2/v1.0 models."""
    paths = sorted((DATA / "task_summary").glob("*.csv"))
    if not paths:
        sys.exit(f"No task-summary CSVs under {DATA / 'task_summary'}.")
    reference = None
    for path in paths:
        # v0.1 includes the superseded Task 15; it is not the current dataset.
        if BENCHMARK_VERSIONS[path.stem] == "v0.1":
            continue
        with path.open() as handle:
            rows = list(csv.DictReader(handle))
        categories = {row["task_id"]: row["category"] for row in rows}
        if not categories or len(categories) != len(rows):
            sys.exit(f"Empty or duplicate task selection in {path}.")
        if reference is None:
            reference = categories
        elif categories != reference:
            sys.exit(f"{path} has a different task selection or category mapping.")
    if reference is None:
        sys.exit("No current-benchmark task-summary CSVs were found.")
    return reference


def load_metadata(repo: Path) -> list[dict]:
    tasks_dir = repo / "tasks"
    if not tasks_dir.is_dir():
        sys.exit(
            f"No tasks/ directory under {repo}.\n"
            f"Point MDARENA_REPO at a checkout of {REPO_NAME}, e.g.\n"
            f"    MDARENA_REPO=/path/to/{REPO_NAME} python {Path(__file__).name}"
        )
    records = []
    for toml_path in sorted(tasks_dir.glob("*/task.toml")):
        with toml_path.open("rb") as handle:
            records.append(tomllib.load(handle)["metadata"])
    if not records:
        sys.exit(f"Found {tasks_dir} but no task.toml files in it.")
    categories = read_task_categories()
    records = [record for record in records if record["task_id"] in categories]
    if {record["task_id"] for record in records} != set(categories):
        sys.exit(f"Some tasks in {DATA / 'task_summary'} are missing from {tasks_dir}.")
    if any(record["task_type"] != categories[record["task_id"]] for record in records):
        sys.exit(
            "Task metadata categories do not match the manuscript task-summary tables."
        )
    return records


def oklch_hex(L: float, C: float, h_deg: float) -> str:
    """One OKLCH colour as sRGB hex, backing off chroma until it is in gamut.

    Lightness and hue are honoured exactly; chroma is a ceiling rather than a
    target, because the sRGB gamut narrows sharply at both ends of the lightness
    range and a fixed chroma would simply fall outside it there.
    """
    h = math.radians(h_deg)
    while C > 0.005:
        a, b = C * math.cos(h), C * math.sin(h)
        l_component = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
        m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
        s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
        rgb = (
            4.0767416621 * l_component - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l_component + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l_component - 0.7034186147 * m + 1.7076147010 * s,
        )
        if all(0.0 <= u <= 1.0 for u in rgb):
            enc = [
                1.055 * u ** (1 / 2.4) - 0.055 if u > 0.0031308 else 12.92 * u
                for u in rgb
            ]
            return "#%02X%02X%02X" % tuple(round(u * 255) for u in enc)
        C -= 0.004
    return "#FFFFFF"


def draw_pie(ax, counts: collections.Counter, title: str, panel: str) -> None:
    """A partition, largest slice first, starting at 12 o'clock."""
    items = counts.most_common()
    n_coloured = sum(1 for v, _ in items if v != "none")
    ramp = [
        CATEGORICAL[i] if i < len(CATEGORICAL) else FALLBACK_COLOUR
        for i in range(n_coloured)
    ]
    colours, k = [], 0
    for value, _ in items:
        if value == "none":
            colours.append(FALLBACK_COLOUR)
        else:
            colours.append(ramp[k])
            k += 1
    # Percentages are drawn inside the wedges, but only where a wedge is wide
    # enough to hold the text; below that they collide with their neighbours and
    # with the pie edge. The suppressed ones are the 1-task slices, whose count is
    # already in the legend.
    wedges, _, pct_texts = ax.pie(
        [n for _, n in items],
        colors=colours,
        radius=PIE_RADIUS,
        startangle=90,
        counterclock=False,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= PCT_LABEL_MIN else "",
        pctdistance=0.68,
        wedgeprops={"edgecolor": "white", "linewidth": 1.0},
        textprops={"fontsize": 9.5},
    )
    # Dark wedges need light text and vice versa, so pick by luminance rather
    # than fixing one colour that fails at one end of the ramp.
    for text, colour in zip(pct_texts, colours):
        r, g, b = matplotlib.colors.to_rgb(colour)
        text.set_color(
            "white" if (0.299 * r + 0.587 * g + 0.114 * b) < 0.55 else "#222222"
        )
    # Keep the legend below the pie in two columns to limit the figure's height.
    ax.legend(
        wedges,
        [f"{label(v)} ({n})" for v, n in items],
        loc="upper center",
        bbox_to_anchor=(0.5, LEGEND_TOP),
        frameon=False,
        fontsize=8.5,
        ncol=2,
        columnspacing=0.6,
        handlelength=0.9,
        handletextpad=0.4,
        borderpad=0.0,
        labelspacing=0.35,
    )
    ax.set_title(title, fontsize=TITLE_SIZE, pad=4)
    ax.set_aspect("equal")
    # Align the square pie axes with the top of the bar panel.
    ax.set_anchor("N")
    panel_label(ax, panel)


def draw_bars(ax, counts: collections.Counter, panel: str) -> list[str]:
    """Multi-valued, so bars rather than a pie: these deliberately do not sum to 50.

    Returns the packages held back for the caption, so they are named somewhere
    rather than collapsed into an anonymous "Other" bar.
    """
    held_back = [v for v, n in counts.most_common() if n < MIN_PACKAGE_COUNT]
    shown = [(v, n) for v, n in counts.most_common() if n >= MIN_PACKAGE_COUNT]
    # Package names are canonical project names already ("GROMACS", "MDAnalysis",
    # "RDKit"), so they are used verbatim - passing them through `label()` would
    # lowercase them into "Gromacs", "Mdanalysis", "Rdkit".
    # "Others" is pinned to the bottom rather than sorted by size, so it reads as
    # a residual rather than as a package that happens to rank between two others.
    items = shown[::-1]
    if held_back and POOL_OTHERS:
        items = [
            (f"Others ({len(held_back)} packages)", sum(counts[v] for v in held_back))
        ] + items
    names = [v for v, _ in items]
    values = [n for _, n in items]
    ax.barh(names, values, color=BAR_COLOUR, height=BAR_HEIGHT)
    for y, v in enumerate(values):
        ax.text(v + max(values) * 0.02, y, str(v), va="center", fontsize=8)
    ax.set_xlim(0, max(values) * 1.12)
    ax.set_xlabel("Number of tasks", fontsize=9, labelpad=2)
    ax.set_title("Software packages", fontsize=TITLE_SIZE, pad=4)
    ax.tick_params(axis="y", labelsize=8)
    ax.tick_params(axis="x", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    panel_label(ax, panel)
    return held_back


def main() -> int:
    override = os.environ.get("MDARENA_REPO")
    repo = Path(override).expanduser() if override else find_repo()
    if repo is None:
        sys.exit(
            f"Found no {REPO_NAME} checkout with a tasks/ directory in or above\n"
            f"    {HERE}\n"
            f"Point MDARENA_REPO at one, e.g.\n"
            f"    MDARENA_REPO=/path/to/{REPO_NAME} python {Path(__file__).name}"
        )
    records = load_metadata(repo)

    task_types = collections.Counter(r["task_type"] for r in records)
    packages = collections.Counter(p for r in records for p in r["packages"])

    # Keep the two remaining panels side by side in a compact layout.
    fig = plt.figure(figsize=(9.0, 3.8))
    grid = GridSpec(1, 2, width_ratios=[1.0, 1.15], wspace=0.55, figure=fig)
    draw_pie(fig.add_subplot(grid[0, 0]), task_types, "Task type", "A")
    held_back = draw_bars(fig.add_subplot(grid[0, 1]), packages, "B")

    fig.savefig(f"{OUT_STEM}.png", dpi=600, bbox_inches="tight", transparent=True)
    fig.savefig(f"{OUT_STEM}.pdf", bbox_inches="tight", transparent=True)

    # Print what was plotted. A figure regenerated against a changed dataset
    # should announce the change rather than quietly look different.
    print(f"Read {len(records)} tasks from {repo}")
    print(f"  Task selection and categories match {DATA / 'task_summary'}")
    print("  task_type: " + ", ".join(f"{v}={n}" for v, n in task_types.most_common()))
    print(f"  packages: {len(packages)} distinct, {sum(packages.values())} assignments")
    if held_back:
        print(
            f"\n  Caption text for the {len(held_back)} packages held back from panel B:\n"
            f"    Exercised by one task each: "
            + ", ".join(sorted(held_back, key=str.lower))
            + "."
        )
    print(f"Wrote {OUT_STEM}.png and {OUT_STEM}.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
