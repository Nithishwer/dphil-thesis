from pathlib import Path
import csv
from typing import Optional, Tuple

import matplotlib

matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patheffects

CHAPTER_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CHAPTER_DIR / "data/compound_reus"
FIGURE_DIR = CHAPTER_DIR / "figures/apo_state_correction"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

# --- Nice default rcParams for publication quality ---
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "figure.figsize": (9, 6),
        "font.family": "roboto",
        "font.serif": ["DejaVu Serif", "Times New Roman", "serif"],
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "axes.linewidth": 1.0,
        "axes.grid": False,
        "legend.fontsize": 10,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 6,
        "ytick.major.size": 6,
        "xtick.minor.size": 3,
        "ytick.minor.size": 3,
        "lines.solid_capstyle": "round",
    }
)


def read_coor_free(path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Read columns (coor, free) from the given file, skipping '#' comment lines."""
    data = np.loadtxt(path, comments="#", usecols=(0, 1))
    if data.ndim == 1:
        data = data.reshape(1, -1)

    x = data[:, 0]
    y = data[:, 1]

    order = np.argsort(x)

    # Convert kJ/mol to kcal/mol
    y = y * 0.239  # * 0.239

    return x[order], y[order]


def read_intersection_points(
    csv_path: str, holo_key: str = "4g_van1", apo_key: str = "apo_3"
) -> Tuple[Optional[float], Optional[float]]:
    """
    Read the intersection CSV and return (holo_x, apo_x).
    Collects all 'coor' values where line_type equals holo_key or apo_key and returns their mean.
    """
    holo_vals = []
    apo_vals = []
    with open(csv_path, newline="") as fh:
        rdr = csv.DictReader(fh)
        for row in rdr:
            if "coor" not in row or "line_type" not in row:
                continue
            try:
                coor = float(row["coor"])
            except (ValueError, TypeError):
                continue
            lt = row["line_type"].strip()
            if lt == holo_key:
                holo_vals.append(coor)
            elif lt == apo_key:
                apo_vals.append(coor)

    holo_x = float(np.mean(holo_vals)) if holo_vals else None
    apo_x = float(np.mean(apo_vals)) if apo_vals else None
    return holo_x, apo_x


def plot_free_and_shaded_with_lines(
    file_60_forward: str,
    file_60_reverse: str,
    file_80_forward: str,
    file_80_reverse: str,
    file_100_forward: str,
    intersection_csv: str,
    holo_key: str = "4g_van1",
    apo_key: str = "apo_3",
    figsize: Tuple[int, int] = (9, 6),
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    annotate_intersections: bool = True,
    savepath: Optional[str] = None,
    save_format: str = "pdf",  # "pdf", "png", "svg" etc.
    # NEW args:
    font_name: Optional[str] = None,
    primary_color: str = "#333333",  # color for 100% forward line
    color_80: str = "#1f77b4",  # color (shade) for 80% shaded region
    color_60: str = "#9ecae1",  # color (shade) for 60% shaded region
    compound: str = "4g",
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Read the 5 data files, plot the 100% forward curve and shade between forward & reverse
    for 80% and 60%. Draw vertical lines for holo and apo using the intersection CSV.

    New parameters:
      - font_name: when provided, temporarily uses this serif font for the figure
      - primary_color, color_80, color_60: colors used for primary line and the two shaded regions
      - vertical lines (holo/apo) are drawn in grey (0.4)

    Returns (fig, ax). If savepath is provided, the plot is saved using save_format.
    """
    # --- read data files ---
    x60_f, y60_f = read_coor_free(file_60_forward)
    x60_r, y60_r = read_coor_free(file_60_reverse)
    x80_f, y80_f = read_coor_free(file_80_forward)
    x80_r, y80_r = read_coor_free(file_80_reverse)
    x100_f, y100_f = read_coor_free(file_100_forward)

    # --- read intersection points ---
    holo_x, apo_x = read_intersection_points(
        intersection_csv, holo_key=holo_key, apo_key=apo_key
    )

    # Use a temporary rc_context to apply font_name if provided (won't permanently alter global rcParams)
    rc_settings = {}
    if font_name:
        # prefer serif family when a font_name is provided
        rc_settings["font.family"] = "serif"
        rc_settings["font.serif"] = [
            font_name,
            "DejaVu Serif",
            "Times New Roman",
            "serif",
        ]

    with plt.rc_context(rc_settings):
        # --- create figure / axes with high-quality defaults ---
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Plot 100% forward curve (primary line) using primary_color
        (primary_line,) = ax.plot(
            x100_f,
            y100_f,
            lw=2.2,
            color=primary_color,
            zorder=10,
            solid_capstyle="round",
        )

        # neat path effect (subtle outline improves visibility on white background)
        primary_line.set_path_effects(
            [patheffects.withStroke(linewidth=2.8, foreground="white", alpha=0.9)]
        )

        # shading helper (interpolate reverse onto forward x-grid)
        def shade_between(xf, yf, xr, yr, label, base_color, alpha=0.35, zorder=1):
            order_r = np.argsort(xr)
            xr_sorted = xr[order_r]
            yr_sorted = yr[order_r]
            yr_interp = np.interp(xf, xr_sorted, yr_sorted, left=np.nan, right=np.nan)
            valid = np.isfinite(yr_interp) & np.isfinite(yf)
            if np.any(valid):
                poly = ax.fill_between(
                    xf[valid],
                    yf[valid],
                    yr_interp[valid],
                    color=base_color,
                    alpha=alpha,
                    linewidth=0,
                    zorder=zorder,
                )
                return poly
            return None

        # use user-provided colors for the shaded regions
        shade_between(
            x80_f,
            y80_f,
            x80_r,
            y80_r,
            label="80% forward/reverse",
            base_color=color_80,
            alpha=0.45,
            zorder=3,
        )
        shade_between(
            x60_f,
            y60_f,
            x60_r,
            y60_r,
            label="60% forward/reverse",
            base_color=color_60,
            alpha=0.30,
            zorder=2,
        )

        # Determine a stable y-range from data for annotation placement
        all_y = np.concatenate([y100_f, y80_f, y80_r, y60_f, y60_r])
        finite_y = all_y[np.isfinite(all_y)]
        if finite_y.size:
            y_min_data = float(np.nanmin(finite_y))
            y_max_data = float(np.nanmax(finite_y))
        else:
            y_min_data, y_max_data = 0.0, 1.0
        # small margin
        y_span = y_max_data - y_min_data
        if y_span <= 0:
            y_span = max(abs(y_max_data), 1.0)
        # compute annotation y positions
        y_holo_annot = y_max_data - 0.10 * y_span
        y_apo_annot = y_max_data - 0.25 * y_span

        # --- vertical lines for holo and apo (kept in grey) ---
        vline_color = "0.4"  # grey (0=black, 1=white). picked medium-dark grey
        vline_kwargs = dict(
            linestyle="--", linewidth=1.25, alpha=0.9, color=vline_color
        )
        if holo_x is not None:
            ax.axvline(holo_x, zorder=12, **vline_kwargs)
            if annotate_intersections:
                # annotate slightly to the right of the vertical line
                ax.annotate(
                    "Holo",
                    xy=(holo_x, y_holo_annot),
                    xytext=(6, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=10,
                    color=vline_color,
                    zorder=14,
                )
        else:
            print(f"Warning: holo point '{holo_key}' not found in {intersection_csv}")

        if apo_x is not None:
            ax.axvline(apo_x, zorder=12, **vline_kwargs)
            if annotate_intersections:
                ax.annotate(
                    "Apo",
                    xy=(apo_x, y_apo_annot),
                    xytext=(6, 0),
                    textcoords="offset points",
                    ha="left",
                    va="center",
                    fontsize=10,
                    color=vline_color,
                    zorder=14,
                )
        else:
            print(f"Warning: apo point '{apo_key}' not found in {intersection_csv}")

        # Optionally mark where the vertical lines cross the 100% curve (if within range) with grey dots
        dot_kwargs = dict(
            marker="o", s=40, color=vline_color, edgecolor="white", zorder=15
        )
        if holo_x is not None and x100_f.min() <= holo_x <= x100_f.max():
            y_holo_on_curve = np.interp(holo_x, x100_f, y100_f)
            ax.scatter([holo_x], [y_holo_on_curve], **dot_kwargs)
        if apo_x is not None and x100_f.min() <= apo_x <= x100_f.max():
            y_apo_on_curve = np.interp(apo_x, x100_f, y100_f)
            ax.scatter([apo_x], [y_apo_on_curve], **dot_kwargs)

        # Labels, grid, ticks
        ax.set_xlabel("CV", fontsize=12)
        ax.set_ylabel("Free Energy (kcal/mol)", fontsize=12)
        ax.set_title(f"{compound}", fontsize=14, pad=12)

        # --- Clean, consistent ticks (same number across plots) ---
        n_ticks = 6  # fixed number of major ticks

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        # Create evenly spaced ticks
        x_major = np.linspace(xmin, xmax, n_ticks)
        y_major = np.linspace(ymin, ymax, n_ticks)

        # Round to nearest even integers
        x_major = 2 * np.round(x_major / 2)
        y_major = 2 * np.round(y_major / 2)

        # Remove duplicates (can happen after rounding)
        x_major = np.unique(x_major)
        y_major = np.unique(y_major)

        # Minor ticks = midpoints (odd positions naturally emerge)
        x_minor = (x_major[:-1] + x_major[1:]) / 2
        y_minor = (y_major[:-1] + y_major[1:]) / 2

        # Apply ticks
        ax.set_xticks(x_major)
        ax.set_xticks(x_minor, minor=True)
        ax.set_yticks(y_major)
        ax.set_yticks(y_minor, minor=True)

        # Styling
        ax.tick_params(axis="both", which="major", labelsize=11)
        ax.tick_params(axis="both", which="minor", labelsize=9)

        # Apply user-specified axis limits if provided (otherwise use data-driven)
        if xlim is not None:
            ax.set_xlim(*xlim)
        if ylim is not None:
            ax.set_ylim(*ylim)
        else:
            # if user didn't specify y-limits, keep a small margin around data
            ax.set_ylim(y_min_data - 0.03 * y_span, y_max_data + 0.03 * y_span)

        # Remove legend (user requested)
        # (intentionally do not call ax.legend())

        # Final layout tweaks
        plt.tight_layout()

        # Save file if requested (vector preferred)
        if savepath:
            ext = save_format.lower()
            save_kwargs = {"bbox_inches": "tight"}
            if ext in ("png", "jpg", "jpeg"):
                fig.savefig(savepath, dpi=600, **save_kwargs)
            else:
                # vector formats (pdf, svg) – keep default dpi
                fig.savefig(savepath, format=ext, **save_kwargs)
            print(f"Saved plot to {savepath}")

    return fig, ax


# Example usage:
if __name__ == "__main__":
    for cmp in ["4g", "4h", "4i", "4j", "4k", "4l", "4m", "4n", "4q", "4r"]:
        fig, ax = plot_free_and_shaded_with_lines(
            file_60_forward=DATA_DIR / f"free_{cmp}_60_pct_forward.dat",
            file_60_reverse=DATA_DIR / f"free_{cmp}_60_pct_reverse.dat",
            file_80_forward=DATA_DIR / f"free_{cmp}_80_pct_forward.dat",
            file_80_reverse=DATA_DIR / f"free_{cmp}_80_pct_reverse.dat",
            file_100_forward=DATA_DIR / f"free_{cmp}_100_pct_forward.dat",
            intersection_csv=DATA_DIR / f"intersection_points_{cmp}_van1_apo_3.csv",
            holo_key=f"{cmp}_van1",
            apo_key="apo_3",
            figsize=(5, 4),
            xlim=None,
            ylim=None,
            annotate_intersections=True,
            savepath=FIGURE_DIR / f"free_vs_coor_{cmp}_van1_apo_3.png",
            save_format="png",
            compound=f"{cmp}",
        )
