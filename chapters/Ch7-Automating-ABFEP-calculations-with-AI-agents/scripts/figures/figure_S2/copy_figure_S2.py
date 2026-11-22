"""Copy the existing twelve-configuration heatmap byte for byte; never replot it."""

import hashlib
import json
import re
import shutil
from pathlib import Path

CHAPTER = Path(__file__).resolve().parents[3]
HERE = CHAPTER / "figures/figure_S2"
REPO = CHAPTER
SOURCE = (
    REPO
    / "figures/analysis/task39_policy_b_2026-11-20/current/figures/task_heatmap_all_twelve"
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    copies = []
    for suffix in [".pdf", ".png"]:
        source = SOURCE.with_suffix(suffix)
        destination = HERE / f"figure_S2{suffix}"
        if destination.exists() and destination.read_bytes() != source.read_bytes():
            raise RuntimeError(
                f"Refusing to overwrite different existing material: {destination}"
            )
        if not destination.exists():
            shutil.copyfile(source, destination)
        assert source.read_bytes() == destination.read_bytes()
        copies.append(
            {
                "source": str(source.relative_to(REPO)),
                "destination": str(destination.relative_to(REPO)),
                "sha256": sha256(source),
                "byte_identical": True,
            }
        )
    # TeX numbering is implicit: flag its existing second figure, without changing it.
    blocks = re.findall(
        r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}",
        (REPO / "data/source/SI.tex").read_text(),
        flags=re.S,
    )
    existing_s2 = None
    if len(blocks) > 1:
        match = re.search(
            r"\\(?:suppfigure|includegraphics(?:\[[^]]*\])?)\{([^}]+)\}", blocks[1]
        )
        existing_s2 = (
            match.group(1) if match else "second figure has no recognized asset"
        )
    conflict = (
        existing_s2 is not None and existing_s2 != "figures/figure_S2/figure_S2.pdf"
    )
    record = {
        "copies": copies,
        "existing_implicit_S2_in_SI": existing_s2,
        "numbering_conflict": conflict,
        "tex_modified": False,
        "note": "New named assets only; existing SI figures and their numbering are untouched.",
    }
    (REPO / "data/figures/figure_S2/copy_manifest.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(
        "Copied PDF and PNG byte-identically; no content, style or annotations changed."
    )
    if conflict:
        print(
            f"Numbering conflict retained for manual resolution: SI currently calls {existing_s2} Figure S2."
        )


if __name__ == "__main__":
    main()
