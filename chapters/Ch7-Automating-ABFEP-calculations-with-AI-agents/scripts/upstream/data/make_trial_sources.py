"""Index the exact exported trials without modifying saved evaluation runs.

Run with Python 3.9+ from any directory. Reads this repository's trial CSVs,
the v0.2 collection manifests, v0.1 task/job maps, and the DD input audit.
Validates all selected result paths before writing data/trial_sources.csv.
"""

import collections
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE = Path("/biggin/b211/reub0138/Projects/LLMsxFEP")
EVAL = REPO.parent / "MDArena_eval"
sys.path.insert(0, str(REPO / "figures"))
from benchmark_versions import BENCHMARK_VERSIONS  # noqa: E402

audit_path = BASE / "MDArena_run_analysis_DD/input-audit.json"
audit = json.loads(audit_path.read_text())
audited_sources = {r["input"]: r["source"] for r in audit["selected"]}
archive_names = {
    "gpt-5.6-sol": "GPT5.6-sol",
    "gpt-5.6-terra": "GPT5.6-terra",
    "opus-5": "Opus-5",
    "sonnet-5": "Sonnet-5",
    "gemini-3.7-flash": "Gemini-3.7-flash",
    "glm-5.2": "GLM-5.2",
    "qwen3-coder-480b": "Qwen3-Coder-480B",
}
index, issues = [], []
for table in sorted((REPO / "data/trials").glob("*.csv")):
    label = table.stem
    version = BENCHMARK_VERSIONS[label]
    rows = list(csv.DictReader(table.open()))
    repeats = 1 if version == "v0.1" else 3
    counts = collections.Counter(row["task_id"] for row in rows)
    assert len(counts) == 50 and set(counts.values()) == {repeats}, label
    mapping = None
    if version == "v0.1":
        mapping_path = Path(rows[0]["jobs_root"]).parent / "analysis/task_job_map.csv"
        mapping = {r["trial_name"]: r for r in csv.DictReader(mapping_path.open())}
        assert len(mapping) == 50
    if label in archive_names:
        archive = BASE / "MDArena_v2_runs/reduced_outputs" / archive_names[label]
        manifest_path = archive / "collect-manifest.json"
        sources = [Path(p) for p in json.loads(manifest_path.read_text())["sources"]]
    for row in rows:
        run_name = row["run_label"].split("/")[-1]
        archived_trial = Path(row["jobs_root"]) / run_name / row["trial_name"]
        selection = ""
        if mapping is not None:
            source = Path(mapping[row["trial_name"]]["job_dir"])
            assert source == archived_trial
            selection = str(mapping_path)
        elif label in archive_names:
            root_name = Path(row["jobs_root"]).name
            source_root = next(p for p in sources if p.name == root_name)
            # MDArena_eval was reorganized after these compact archives were made.
            if str(source_root).startswith(str(EVAL) + "/"):
                source_root = EVAL / "v0.2" / source_root.relative_to(EVAL)
            source = (
                source_root / row["trial_name"] if root_name == run_name else source_root / run_name / row["trial_name"]
            )
            selection = str(manifest_path)
        elif str(archived_trial) in audited_sources:
            source = Path(audited_sources[str(archived_trial)])
            selection = str(audit_path)
        else:
            source = archived_trial.resolve()
        for kind, trial in [("analysis", archived_trial), ("source", source)]:
            if not (trial / "result.json").is_file():
                issues.append((label, kind, str(trial)))
        index.append(
            {
                "model": label,
                "benchmark_version": version,
                "harness": row["agent_name"],
                "task_id": row["task_id"],
                "attempt_index": row["attempt_index"],
                "trial_name": row["trial_name"],
                "analysis_trial_dir": str(archived_trial),
                "source_trial_dir": str(source),
                "selection_record": selection,
            }
        )
    print(label, len(rows), "trials indexed", flush=True)

assert len(index) == 2100
assert len({(r["model"], r["task_id"], r["attempt_index"]) for r in index}) == 2100
if issues:
    raise SystemExit(f"Missing {len(issues)} selected result paths: {issues[:5]}")
print("All 2100 analysis results and 2100 source results exist.", flush=True)
out = REPO / "data/trial_sources.csv"
with out.open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(index[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(index)
print("Wrote", out, flush=True)
