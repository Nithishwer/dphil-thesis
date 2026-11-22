# Figure 1 — caption

## Caption

**Figure 1. Composition of the MDArena dataset.**
**(A)** Task type, the kind of work each task asks the agent to do. One value per
task, so the 50 tasks are partitioned exactly once.
**(B)** System type, what is being simulated. Also a partition of the 50 tasks;
`No molecular system` is `42_expanded_ensemble_mdp`, which operates on a GROMACS
MDP file alone.
**(C)** Software packages exercised by the tasks. Unlike (A) and (B) a task may
use several packages, so the bars sum to 111 assignments rather than to 50; they
are drawn as bars rather than a pie for that reason. Seven further packages are
each exercised by exactly one task and are omitted from the axis for legibility:
alchemlyb, ensemble_md, MDRestraintsGenerator, openmmforcefields, ORCA,
physical_validation and ProLIF. Counting those, the benchmark exercises 18
packages in total.
All three panels are generated directly from the `[metadata]` block of each
task's `task.toml`, the same values the benchmark's validator enforces.

## Notes for us, not for the paper

**Why (C) is bars and not a pie.** The chart type is doing work. (A) and (B) are
partitions and sum to 50; (C) does not. Drawing all three as pies would imply
the third also sums to 50.

**Why there is no "Others" bar.** Every bar in (C) means "number of tasks using
this package". An Others bar would mean "number of tasks using any of seven
packages" — a different quantity on the same axis, which invites comparison
against PLUMED or ParmEd as though Others were a single package. Worse, the
pooled bar would have length 7 and the label "7 packages", two unrelated sevens
on one row. The seven are named in the caption instead, so nothing is hidden.
Set `POOL_OTHERS = True` in `make_figure_1.py` to draw the bar anyway, or
`MIN_PACKAGE_COUNT = 1` to list all 18 on the axis.

**Numbers that changed from v1 and will be queried.**

- 18 packages, not the manuscript's 22. Generic scientific Python (NumPy,
  matplotlib, pandas, MPI) is excluded, so this counts biomolecular MD software
  only. `openmmtools`, `pymbar` and `MDTraj` appeared in the v1 package table but
  appear nowhere in the repository.
- Task types are 7, not the 12 categories of v0.1 or the 14 method classes of the
  v1 figure. Those two lists were maintained separately and disagreed with each
  other; see `docs/DATASET_VERSIONS.md` in MDArena-dev for the mapping.
- Membrane protein is 60% of (B). That is accurate and is the reason
  membrane-protein preparation is the benchmark's hardest category, but expect a
  reviewer to note the imbalance.

**Regenerating.** `python make_figure_1.py`, or with an explicit checkout:
`MDARENA_REPO=/path/to/MDArena-dev python make_figure_1.py`. The script prints the
counts it plotted, so a regeneration against changed task metadata announces the
change rather than quietly producing a different figure.
