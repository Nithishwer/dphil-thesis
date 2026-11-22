# Approved Task 39 Policy B

This local overlay applies Wei-Tse's explicit approval in the conversation.
It was rebuilt against commit `b2f616bf8318c6cfa0d1c24804824f9bb6f8b6ad` after
the repository update removed the previous untracked implementation and follow-up.
No Policy A changes were present in the current input scores.

`decision.json` identifies all 36 selected repeated trials by UUID, exact trial
name, task checksum, task ID and replicate. `criterion_decisions.csv` records all
390 scored decisions for the 26 completed setups. C6, P2 and ion-specific P4
remain scored failures; accepted non-charge decisions are carried forward without
new artifact validation. `trial_changes.csv` lists the 16 changed score pairs.
The other ten completed setups already had correctness 0.9 and process 0.6.
The nine execution-error trials retain their raw grades; adjusted metrics score
errors zero. The completed empty GLM trial is unchanged.

The original focused report was removed by the reset. The recovered approval
basis in `analysis/section3_followup_2026-11-20/` is explicitly identified as a
reconstruction from the surviving first-review provenance and saved original/final
criterion records. It is not a verbatim restoration or a new grading. Older final
criterion values remain marked unavailable where only aggregate exports survive.

Original run/grade records and canonical tasks are unchanged. Task 35 and the
separate ion-order investigation are outside this update. **All TeX files remain
unchanged**, following the user's latest instruction; required manual text updates
are listed in the new analysis report. Pre-update CSVs are in
`analysis/task39_policy_b_2026-11-20/before/data/`.

Replay after importing upstream exports, with the existing environment:

```bash
PYTHONDONTWRITEBYTECODE=1 ../MDArena-dev/.venv/bin/python data/apply_task39_policy_b.py
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mdarena-matplotlib ../MDArena-dev/.venv/bin/python analysis/task39_policy_b_2026-11-20/regenerate.py
```

The overlay verifies exact identities and refuses unexpected score drift. It
reuses MDArena's existing aggregation/export functions: 2,000 task-clustered
bootstrap resamples, seed 0, 95% percentile intervals. The legacy `pass_rate`
keeps its correctness-only conditional meaning; strict success requires both
dimensions and completion. Recorded costs, all 2,100 selected trials and the six
historical v0.1 configurations are preserved. Publication/SI assets retain their
selections and styles. Updated exploratory outputs are in the new `current/`
directory; the surviving earlier review remains a frozen historical snapshot.
