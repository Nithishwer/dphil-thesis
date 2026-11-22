#!/usr/bin/env python3
"""Figure S1: Figure 3's analysis for the nine remaining configurations.

Reuse Figure 3's renderer, strict-pass definition, task bootstrap, and cost
handling, including Qwen3 Coder's supplied mean cost from the workshop paper.
"""

from pathlib import Path
from make_figure_4 import main

CHAPTER = Path(__file__).resolve().parents[1]
HERE = CHAPTER / "figures/figure_S1"

MODELS = [
    ("gpt-5.5-medium", "GPT-5.5 Medium", "o"),
    ("gpt-5.5-xhigh", "GPT-5.5 XHigh", "^"),
    ("gpt-5.6-terra", "GPT-5.6 Terra", "o"),
    ("sonnet-5", "Claude Sonnet-5", "o"),
    ("gemini-3.5-flash", "Gemini 3.5 Flash", "o"),
    ("gemini-3.1-pro-preview", "Gemini 3.1 Pro Preview", "^"),
    ("deepseek-v3.2", "DeepSeek V3.2", "o"),
    ("qwen3-235b-a22b-instruct-2507", "Qwen3 Instruct 235B A22B", "^"),
    ("qwen3-coder-480b", "Qwen3 Coder 480B A35B", "s"),
]

# Match Figure 3's provider hues, using shades to distinguish configurations.
MODEL_COLOURS = [
    "#B7DFCF",
    "#88C8B2",
    "#12614F",
    "#E88E70",
    "#F2D46F",
    "#BD8B13",
    "#3C5773",
    "#849DB7",
    "#B4C5D6",
]


if __name__ == "__main__":
    raise SystemExit(main(MODELS, MODEL_COLOURS, HERE / "figure_S1", legend_columns=3))
