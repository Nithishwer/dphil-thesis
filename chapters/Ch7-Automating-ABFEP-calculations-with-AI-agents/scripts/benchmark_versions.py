"""Benchmark cohorts used in the manuscript's figures and trial index."""

# These are manuscript cohort labels, not the v2/v3/v4 run-folder names.
BENCHMARK_VERSIONS = {
    "gpt-5.5-medium": "v0.1",
    "gpt-5.5-xhigh": "v0.1",
    "gemini-3.5-flash": "v0.1",
    "gemini-3.1-pro-preview": "v0.1",
    "deepseek-v3.2": "v0.1",
    "qwen3-235b-a22b-instruct-2507": "v0.1",
    "gpt-5.6-sol": "v0.2",
    "gpt-5.6-terra": "v0.2",
    "opus-5": "v0.2",
    "sonnet-5": "v0.2",
    "gemini-3.7-flash": "v0.2",
    "glm-5.2": "v0.2",
    "qwen3-coder-480b": "v0.2",
    "gpt-6.1-sol": "v1.0",
    "gpt-6-astra": "v1.0",
    "opus-5.5": "v1.0",
    "gemini-4-argon": "v1.0",
    "deepseek-v4": "v1.0",
}


def marked_name(label: str, display: str) -> str:
    """Append a superscript star for v0.2 or dagger for v0.1."""
    symbol = {"v0.1": r"\dagger", "v0.2": "*"}.get(BENCHMARK_VERSIONS[label])
    return display if symbol is None else f"{display}$^{{{symbol}}}$"
