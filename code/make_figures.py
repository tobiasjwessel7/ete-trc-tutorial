"""Reproducible manuscript figures, presentation revision 2026-09-29.

Run from any working directory after installing ../requirements.txt:
    python3 code/make_figures.py                  # all four figures
    python3 code/make_figures.py --figures 1 2 3   # keep existing Figure 4

Reads the existing result CSVs; never runs simulations or writes data/results.
Outputs vector PDF, 300-dpi PNG and 600-dpi LZW TIFF. Figure 3 is assembled
from three separately drawn charts, also supplied in figures/panels/.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
FIG = ROOT / "figures"
MM = 1 / 25.4

# Figure 4 retains its original settings and drawing code.
NAVY, TEAL, ORANGE, GREEN, GREY = "#1F3B5C", "#1B8A8A", "#E07B22", "#3E8E41", "#7A7F87"
NAVY_L, TEAL_L, ORANGE_L, GREEN_L, GREY_L = "#DCE4EE", "#D5EDED", "#FBE6D3", "#DDEEDD", "#ECEDEF"
LEGACY_STYLE = {
    "font.family": "Liberation Sans", "font.size": 8, "axes.titlesize": 9,
    "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.spines.top": False,
    "axes.spines.right": False, "pdf.fonttype": 42,
}
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 8, "font.weight": "normal",
    "text.color": "black", "axes.labelcolor": "black",
    "axes.titlesize": 8.5, "axes.titleweight": "bold", "axes.labelsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "xtick.color": "black", "ytick.color": "black",
    "axes.edgecolor": "black", "axes.linewidth": 0.65,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": False, "lines.linewidth": 0.9,
    "lines.markersize": 2.8, "lines.markeredgewidth": 0.65,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.facecolor": "white", "savefig.facecolor": "white",
}
LAYOUT_CHECKS: list[dict] = []
PLOT_SERIES: list[dict] = []


@contextmanager
def style_context(style: dict):
    """Isolate the revised style from Figure 4 and user matplotlib settings."""
    with plt.rc_context():
        plt.rcdefaults()
        plt.rcParams.update(style)
        yield


def _check_layout(fig: Figure, name: str) -> None:
    """Fail rather than silently export clipped text or a legend over data."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    page = fig.bbox
    errors = []
    texts = [x for x in fig.findobj(matplotlib.text.Text)
             if x.get_visible() and x.get_text().strip()]
    for txt in texts:
        # Empty offset labels and unused tick labels are not informative.
        b = txt.get_window_extent(renderer)
        if b.width <= 0 or b.height <= 0:
            continue
        if (b.x0 < page.x0 - 0.75 or b.y0 < page.y0 - 0.75 or
                b.x1 > page.x1 + 0.75 or b.y1 > page.y1 + 0.75):
            errors.append(f"Text outside page: {txt.get_text()!r}")
    for txt, bounds in getattr(fig, "_text_regions", []):
        b = txt.get_window_extent(renderer)
        x0, y0, x1, y1 = bounds
        p0 = txt.axes.transData.transform((x0, y0))
        p1 = txt.axes.transData.transform((x1, y1))
        left, right = sorted((p0[0], p1[0]))
        bottom, top = sorted((p0[1], p1[1]))
        if (b.x0 < left - 0.75 or b.x1 > right + 0.75 or
                b.y0 < bottom - 0.75 or b.y1 > top + 0.75):
            errors.append(f"Text outside assigned box: {txt.get_text()!r}")
    for ax in fig.axes:
        legend = ax.get_legend()
        if legend is not None and legend.get_window_extent(renderer).overlaps(ax.bbox):
            errors.append("Legend overlaps the plotting area")
    LAYOUT_CHECKS.append({"figure": name, "visible_text_objects": len(texts),
                          "page_and_box_bounds": "pass" if not errors else "fail",
                          "errors": errors})
    if errors:
        raise ValueError(name + ": " + "; ".join(errors))


def save(fig: Figure, name: str, *, legacy: bool = False) -> None:
    """Save at explicit physical size; tight cropping is legacy-Figure-4 only."""
    FIG.mkdir(parents=True, exist_ok=True)
    dst = FIG / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not legacy:
        _check_layout(fig, name)
    kwargs = {"bbox_inches": "tight"} if legacy else {}
    fig.savefig(str(dst) + ".png", dpi=300, facecolor="white", **kwargs)
    fig.savefig(str(dst) + ".pdf", facecolor="white", **kwargs)
    fig.savefig(str(dst) + ".tiff", dpi=600, facecolor="white",
                pil_kwargs={"compression": "tiff_lzw"}, **kwargs)
    plt.close(fig)


def diagram(width: float, height: float):
    """A full-canvas diagram, with millimetres measured down from the top."""
    fig = plt.figure(figsize=(width * MM, height * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, width), ylim=(height, 0))
    ax.axis("off")
    fig._text_regions = []
    return fig, ax


def label(ax, x: float, y: float, text: str, *, bold: bool = False,
          ha: str = "center", va: str = "center", region=None):
    txt = ax.text(x, y, text, color="black", fontsize=8.5 if bold else 8,
                  fontweight="bold" if bold else "normal", fontstyle="normal",
                  ha=ha, va=va, linespacing=1.24, zorder=5)
    if region is not None:
        ax.figure._text_regions.append((txt, region))
    return txt


def box(ax, x: float, y: float, width: float, height: float,
        *, fill: str = "white", weight: float = 0.75):
    ax.add_patch(FancyBboxPatch((x, y), width, height,
                 boxstyle="round,pad=0,rounding_size=1.25",
                 facecolor=fill, edgecolor="0.3", linewidth=weight, zorder=3))


def rule(ax, xs, ys):
    ax.plot(xs, ys, color="0.3", linewidth=0.8, linestyle="-",
            solid_capstyle="butt", solid_joinstyle="miter", zorder=2)


def arrow(ax, x0: float, y0: float, x1: float, y1: float):
    """Solid shaft and filled arrowhead, identical throughout Figures 1-2."""
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
        arrowstyle="-|>", mutation_scale=7, color="0.3",
        linestyle="-", linewidth=0.8, shrinkA=0, shrinkB=0, zorder=4))


def figure1() -> None:
    with style_context(STYLE):
        fig, ax = diagram(170, 86)
        xs, w = [3, 44.75, 86.5, 128.25], 38.75
        stages = ["Practice\nwith the tool", "Immediate probe\n(novel items)",
                  "Delay\n(days to weeks)", "Delayed test\n(novel items, no tool)"]
        for i, (x, text) in enumerate(zip(xs, stages)):
            box(ax, x, 3, w, 17)
            label(ax, x + w / 2, 11.5, text, region=(x + 1, 4, x + w - 1, 19))
            if i < 3:
                arrow(ax, x + w, 11.5, xs[i + 1], 11.5)
        # Each probe leads to its own question; there is no inferred link
        # from immediate tool advantage to the delayed between-arm effect.
        for origin, target in [(xs[1] + w / 2, 42.5), (xs[3] + w / 2, 127.5)]:
            rule(ax, [origin, origin, target], [20, 24.5, 24.5])
            arrow(ax, target, 24.5, target, 29)
        cards = [
            (3, "Tool-removal cost (TRC)", "What does the tool add right now?",
             "Accuracy\nwith tool", "Accuracy\nwithout tool",
             "Same people, immediate probe."),
            (88, "Epistemic transfer effect (ETE)", "What does the user keep without it?",
             "Unassisted accuracy\nafter assisted\npractice",
             "Unassisted accuracy\nafter comparator\npractice",
             "Between arms, delayed test; no tool."),
        ]
        for x, title, question, left, right, note in cards:
            box(ax, x, 29, 79, 43, fill="0.965")
            label(ax, x + 39.5, 34.2, title, bold=True, region=(x + 2, 30, x + 77, 38))
            label(ax, x + 39.5, 41, question, region=(x + 2, 38, x + 77, 44))
            for bx, text in [(x + 3, left), (x + 42, right)]:
                box(ax, bx, 47, 34, 13, weight=0.65)
                label(ax, bx + 17, 53.5, text, region=(bx + 0.75, 48, bx + 33.25, 59))
            label(ax, x + 39.5, 53.5, "−", bold=True)
            label(ax, x + 39.5, 66.4, note, region=(x + 2, 62, x + 77, 71))
        label(ax, 85, 79.5,
              "Neither quantity identifies the other: a large tool advantage can coexist with\n"
              "strong, absent, or negative retained capability.",
              region=(3, 74, 167, 85))
        save(fig, "fig1_two_estimands")


def figure2() -> None:
    with style_context(STYLE):
        fig, ax = diagram(170, 118)
        # Baseline -> randomisation -> four regimes -> common schedule.
        for x, title, body in [
            (3, "1  Baseline", "Unassisted items; accuracy,\nconfidence and covariates."),
            (91, "2  Random assignment", "One of four practice regimes (A–D)."),
        ]:
            box(ax, x, 3, 76, 18)
            label(ax, x + 38, 8, title, bold=True, region=(x + 2, 4, x + 74, 12))
            label(ax, x + 38, 15, body, region=(x + 2, 11, x + 74, 20))
        arrow(ax, 79, 12, 91, 12)
        xs, w = [3, 44.75, 86.5, 128.25], 38.75
        centers = [x + w / 2 for x in xs]
        rule(ax, [129, 129], [21, 25])
        rule(ax, [centers[0], centers[-1]], [25, 25])
        arms = [
            ("A  Answer-first AI", "Verdict shown before\nthe user judges."),
            ("B  Evidence-first AI", "Evidence work before\nthe verdict."),
            ("C  Active practice", "The same work,\nwithout AI."),
            ("D  No practice", "Matched-duration\nunrelated activity."),
        ]
        for x, cx, (title, body) in zip(xs, centers, arms):
            arrow(ax, cx, 25, cx, 29)
            box(ax, x, 29, w, 19, fill="0.965")
            label(ax, cx, 34, title, bold=True, region=(x + 1, 30, x + w - 1, 38))
            label(ax, cx, 41.5, body, region=(x + 1, 37, x + w - 1, 47))
            rule(ax, [cx, cx], [48, 52])
        rule(ax, [centers[0], centers[-1]], [52, 52])
        # All four regimes, including the matched-duration no-practice arm,
        # enter the same measurement schedule.
        arrow(ax, 28, 52, 28, 58)
        phases = [
            (3, "3  Practice period", "A–C: enough trials or sessions\nfor learning to be possible.\nD: matched-duration activity."),
            (60, "4  Immediate probe", "Novel items; tool on a random\nhalf in AI arms; matched block\nin the other arms."),
            (117, "5  Delayed test", "7–14 days later; novel items;\nnear / mid / far transfer;\nno tool."),
        ]
        for i, (x, title, body) in enumerate(phases):
            box(ax, x, 58, 50, 25)
            label(ax, x + 25, 63, title, bold=True, region=(x + 2, 59, x + 48, 67))
            label(ax, x + 25, 74, body, region=(x + 2, 67, x + 48, 82))
            if i < 2:
                arrow(ax, x + 50, 70.5, phases[i + 1][0], 70.5)
        for x, title, body in [
            (60, "TRC", "With vs. without tool;\nwithin person, at probe."),
            (117, "ETE", "AI arm vs. C and vs. D;\nbetween arms, delayed."),
        ]:
            arrow(ax, x + 25, 83, x + 25, 87)
            box(ax, x, 87, 50, 16, fill="0.965")
            label(ax, x + 25, 91.2, title, bold=True, region=(x + 2, 88, x + 48, 95))
            label(ax, x + 25, 98, body, region=(x + 2, 94, x + 48, 102.5))
        label(ax, 4, 87.5, "Before analysis", bold=True, ha="left", va="top",
              region=(3, 86, 54, 93))
        label(ax, 4, 93, "Audit tool availability, item sets\nand randomised orders.",
              ha="left", va="top", region=(3, 92, 54, 103))
        rule(ax, [3, 167], [106.5, 106.5])
        label(ax, 3, 109, "Report with every ETE: comparator (C and D), delay, test access regime, item novelty,\n"
              "transfer distance, dose, smallest effect of interest, and equivalence decision.",
              ha="left", va="top", region=(3, 108, 167, 117))
        save(fig, "fig2_protocol")


def read_table(filename: str, required: set[str]) -> pd.DataFrame:
    path = RES / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required figure input not found: {path}. "
                                "Restore the supplied results or run the README reproduction steps.")
    table = pd.read_csv(path)
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"{filename}: missing columns {sorted(missing)}")
    return table


def add_series(ax, table: pd.DataFrame, x: str, y: str, label_text: str,
               *, panel: str, source: str, color: str, marker: str,
               linestyle="-", open_marker: bool = False):
    """Plot untouched, sorted source values and log them for inspection."""
    table = table.sort_values(x)
    if table.empty or table[x].duplicated().any():
        raise ValueError(f"{panel}/{label_text}: empty series or duplicate {x} values")
    values = table[[x, y]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{panel}/{label_text}: non-finite plot values")
    ax.plot(table[x], table[y], color=color, linestyle=linestyle,
            marker=marker, markersize=2.8, linewidth=0.9,
            markerfacecolor="white" if open_marker else color,
            markeredgecolor=color, markeredgewidth=0.65, label=label_text,
            clip_on=True)
    for xx, yy in values:
        PLOT_SERIES.append({"panel": panel, "series": label_text.replace("\n", " "),
                            "source": source, "x_variable": x, "y_variable": y,
                            "x": float(xx), "y": float(yy)})


def chart(height: float, title: str):
    """One distinct chart per Figure object; space at right is for its legend."""
    fig = plt.figure(figsize=(170 * MM, height * MM))
    ax = fig.add_axes([17 / 170, 12 / height, 100 / 170, (height - 22) / height])
    ax.set_title(title, loc="left", pad=6)
    ax.tick_params(axis="both", which="major", length=3, width=0.65, pad=3)
    return fig, ax


def outside_legend(ax):
    legend = ax.legend(loc="center left", bbox_to_anchor=(1.055, 0.5),
                       borderaxespad=0, frameon=False, handlelength=2.25,
                       handletextpad=0.7, labelspacing=0.75,
                       markerscale=1, fontsize=8)
    for text in legend.get_texts():
        text.set_color("black")
    return legend


def trc_input() -> tuple[pd.DataFrame, str]:
    # Prefer the 150-replication grid, even if validation_trc.csv is absent.
    if (RES / "validation_trc_grid.csv").is_file():
        a = read_table("validation_trc_grid.csv", {"n", "probe_items", "glmm_halfwidth_pp", "paired_halfwidth_pp"})
        a = a.loc[a.n == 300].rename(columns={"glmm_halfwidth_pp": "glmm_hw", "paired_halfwidth_pp": "paired_hw"})
        source = "validation_trc_grid.csv"
    else:
        t = read_table("validation_trc.csv", {"n", "probe_items", "glmm_hw", "paired_hw"})
        # Do not silently pool sample sizes and then label the result n = 300.
        t = t.loc[t.n == 300]
        a = t.groupby("probe_items", as_index=False)[["glmm_hw", "paired_hw"]].mean()
        source = "validation_trc.csv (means at n=300)"
        warnings.warn("TRC grid absent: using the shorter validation run at n=300.", stacklevel=2)
    if a.empty or set(a.probe_items) != {8, 16, 32}:
        raise ValueError("Figure 3C requires probe-item counts 8, 16, 32 at n=300. "
                         'Run: Rscript validate_trc_grid.R 150 "300" "8,16,32"')
    return a.sort_values("probe_items"), source


def assemble_panels(names: list[str], name: str, gap_mm: float = 3) -> None:
    """Place independent charts on one publication page; retain vector PDFs."""
    try:
        from pypdf import PdfReader, PdfWriter, Transformation
    except ImportError as exc:
        raise RuntimeError("Figure 3 assembly requires pypdf. "
                           "Install the updated requirements.txt first.") from exc
    readers = [PdfReader(str(FIG / (n + ".pdf"))) for n in names]
    pages = [r.pages[0] for r in readers]
    widths = [float(p.mediabox.width) for p in pages]
    if max(widths) - min(widths) > 0.01:
        raise ValueError("Figure 3 panels must have the same physical width")
    gap = gap_mm * MM * 72
    height = sum(float(p.mediabox.height) for p in pages) + gap * (len(pages) - 1)
    writer = PdfWriter()
    canvas = writer.add_blank_page(width=widths[0], height=height)
    y = height
    for page in pages:
        y -= float(page.mediabox.height)
        canvas.merge_transformed_page(page, Transformation().translate(tx=0, ty=y))
        y -= gap
    writer.add_metadata({"/Title": "Figure 3. Power and precision of the ETE and TRC",
                         "/Subject": "Presentation-only revision; source numerical results unchanged"})
    with (FIG / (name + ".pdf")).open("wb") as out:
        writer.write(out)
    # No rescaling, smoothing or replotting in raster assembly.
    for extension, dpi in [("png", 300), ("tiff", 600)]:
        images = []
        for n in names:
            with Image.open(FIG / (n + "." + extension)) as im:
                images.append(im.convert("RGB"))
        if len({im.width for im in images}) != 1:
            raise ValueError("Figure 3 raster-panel widths disagree")
        gap_px = round(gap_mm * MM * dpi)
        out = Image.new("RGB", (images[0].width,
                        sum(im.height for im in images) + gap_px * (len(images) - 1)), "white")
        yy = 0
        for im in images:
            out.paste(im, (0, yy))
            yy += im.height + gap_px
            im.close()
        kwargs = {"compression": "tiff_lzw"} if extension == "tiff" else {}
        out.save(FIG / (name + "." + extension), dpi=(dpi, dpi), **kwargs)
        out.close()


def figure3() -> None:
    g = read_table("ete_power_grid.csv", {"grid", "k_delayed", "true_ete_pp", "n_per_arm",
                  "power_superiority", "power_equivalence", "mean_halfwidth_pp"})
    h = read_table("ete_heterogeneity_grid.csv", {"sigma_slope", "true_ete_pp", "k_delayed",
                  "n_per_arm", "cr_halfwidth_pp"})
    a, trc_source = trc_input()
    main = g.loc[g.grid == "main"]
    with style_context(STYLE):
        fig, ax = chart(58, "A  Power, 24 delayed items")
        for ete, c, marker, ls, opened in [(5, "0.12", "o", "-", False),
                                         (3, "0.4", "^", "--", True)]:
            s = main.loc[(main.k_delayed == 24) & (main.true_ete_pp == ete)]
            add_series(ax, s, "n_per_arm", "power_superiority", f"True ETE = {ete} pp", panel="A",
                       source="ete_power_grid.csv", color=c, marker=marker, linestyle=ls, open_marker=opened)
        s = main.loc[(main.k_delayed == 24) & (main.true_ete_pp == 0)]
        add_series(ax, s, "n_per_arm", "power_equivalence", "Equivalence;\ntrue ETE = 0", panel="A",
                   source="ete_power_grid.csv", color="0.15", marker="s", linestyle="-.", open_marker=True)
        ax.axhline(0.8, color="0.6", linewidth=0.6, linestyle=(0, (2, 3)), zorder=0)
        ax.text(1275, 0.81, "80%", ha="right", va="bottom", fontsize=8, color="black")
        ax.set(xlabel="Participants per arm", ylabel="Power", xlim=(100, 1300), ylim=(0, 1.045),
               xticks=[150, 400, 600, 900, 1250], yticks=[0, 0.2, 0.4, 0.6, 0.8, 1])
        outside_legend(ax)
        save(fig, "panels/fig3A_power")

        fig, ax = chart(70, "B  Precision of the ETE")
        shades, markers = {16: "0.15", 24: "0.4", 32: "0.58"}, {16: "o", 24: "s", 32: "^"}
        for k in (16, 24, 32):
            s = main.loc[(main.k_delayed == k) & (main.true_ete_pp == 0)]
            add_series(ax, s, "n_per_arm", "mean_halfwidth_pp", f"{k} items", panel="B",
                       source="ete_power_grid.csv", color=shades[k], marker=markers[k],
                       open_marker=(k == 24))
        s = g.loc[(g.grid == "sens_su1.6") & (g.true_ete_pp == 0)]
        add_series(ax, s, "n_per_arm", "mean_halfwidth_pp", "24 items;\nparticipant SD = 1.6", panel="B",
                   source="ete_power_grid.csv", color="0.1", marker="D", linestyle="--", open_marker=True)
        h0 = h.loc[np.isclose(h.sigma_slope, 0.3) & (h.true_ete_pp == 0)]
        for k in (16, 32):
            s = h0.loc[h0.k_delayed == k]
            add_series(ax, s, "n_per_arm", "cr_halfwidth_pp", f"{k} items; item-varying\neffect (SD = 0.3)",
                       panel="B", source="ete_heterogeneity_grid.csv", color=shades[k],
                       marker=markers[k], linestyle=":", open_marker=True)
        ax.axhline(5, color="0.6", linewidth=0.6, linestyle=(0, (2, 3)), zorder=0)
        ax.text(1275, 5.12, "SESOI = 5 pp", ha="right", va="bottom", fontsize=8, color="black")
        ax.set(xlabel="Participants per arm", ylabel="95% CI half-width (pp)", xlim=(100, 1300),
               ylim=(0, 6.5), xticks=[150, 400, 600, 900, 1250], yticks=[0, 1, 2, 3, 4, 5, 6])
        outside_legend(ax)
        save(fig, "panels/fig3B_precision_ete")

        fig, ax = chart(58, "C  Precision of the TRC")
        add_series(ax, a, "probe_items", "glmm_hw", "Items as a\nrandom sample", panel="C",
                   source=trc_source, color="0.1", marker="o")
        add_series(ax, a, "probe_items", "paired_hw", "Items ignored", panel="C",
                   source=trc_source, color="0.5", marker="s", linestyle="--", open_marker=True)
        upper = max(8, float(a.glmm_hw.max()) * 1.15)
        ax.set(xlabel="Probe items (n = 300)", ylabel="95% CI half-width (pp)",
               xticks=[8, 16, 32], xlim=(6, 34), ylim=(0, upper))
        outside_legend(ax)
        save(fig, "panels/fig3C_precision_trc")
    assemble_panels(["panels/fig3A_power", "panels/fig3B_precision_ete", "panels/fig3C_precision_trc"],
                    "fig3_power_precision")



import os  # original Figure 4 path handling

def _figure4_original():
    fig, ax = plt.subplots(figsize=(110 * MM, 85 * MM))
    xlim, ylim, sesoi, thr = (-15, 15), (-2, 50), 5, 10
    ax.add_patch(Rectangle((xlim[0], thr), sesoi - xlim[0], ylim[1] - thr, fc=ORANGE_L, ec="none"))
    ax.add_patch(Rectangle((sesoi, thr), xlim[1] - sesoi, ylim[1] - thr, fc=TEAL_L, ec="none"))
    ax.add_patch(Rectangle((xlim[0], ylim[0]), sesoi - xlim[0], thr - ylim[0], fc=GREY_L, ec="none"))
    ax.add_patch(Rectangle((sesoi, ylim[0]), xlim[1] - sesoi, thr - ylim[0], fc=GREEN_L, ec="none"))
    ax.add_patch(Rectangle((-sesoi, ylim[0]), 2 * sesoi, ylim[1] - ylim[0], fc="white", ec="none", alpha=0.35))
    for x in (-sesoi, sesoi): ax.axvline(x, color=GREY, lw=0.8, ls="--")
    ax.axhline(thr, color=GREY, lw=0.8, ls="--")
    ax.text(-14.5, 48, "Capability on loan", color=ORANGE, fontsize=8, fontweight="bold", va="top")
    ax.text(14.5, 48, "Capability + tool advantage", color=TEAL, fontsize=8, fontweight="bold", va="top", ha="right")
    ax.text(-14.5, -1, "Inert / de-skilling", color=GREY, fontsize=8, fontweight="bold", va="bottom")
    ax.text(14.5, -1, "Capability building", color=GREEN, fontsize=8, fontweight="bold", va="bottom", ha="right")
    ax.text(0, 12, "equivalence region\n(±SESOI)", ha="center", va="bottom", fontsize=6.3, color=GREY)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xlabel("Epistemic Transfer Effect vs. active practice (pp, delayed, 95% CI)")
    ax.set_ylabel("Tool-Removal Cost (pp, immediate, 95% CI)")
    pth = os.path.join(RES, "worked_example_results.csv")
    if os.path.exists(pth):
        r = pd.read_csv(pth).set_index("contrast")
        for arm, c, lab, off, ha in [("answer_first_ai", ORANGE, "Answer-first AI", (-7, -13), "right"), ("evidence_first_ai", TEAL, "Evidence-first AI", (7, 9), "left")]:
            e = r.loc[f"ETE_{arm}_vs_active_practice"]; t = r.loc[f"TRC_{arm}"]
            ax.errorbar(e.estimate, t.estimate, xerr=[[e.estimate - e.ci95_lo], [e.ci95_hi - e.estimate]],
                        yerr=[[t.estimate - t.ci95_lo], [t.ci95_hi - t.estimate]], fmt="o", color=c, ms=5, capsize=2.5, lw=1.2)
            ax.annotate(lab, (e.estimate, t.estimate), xytext=off, textcoords="offset points", fontsize=7.5, color=c, fontweight="bold", ha=ha)
    save(fig, "fig4_diagnostic_space", legacy=True)


def figure4() -> None:
    with style_context(LEGACY_STYLE):
        _figure4_original()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--figures", nargs="+", type=int, choices=(1, 2, 3, 4), default=[1, 2, 3, 4],
                        help="Figures to regenerate (default: all). Use 1 2 3 to retain supplied Figure 4.")
    args = parser.parse_args()
    functions = {1: figure1, 2: figure2, 3: figure3, 4: figure4}
    FIG.mkdir(parents=True, exist_ok=True)
    try:
        for number in dict.fromkeys(args.figures):
            functions[number]()
            print(f"Figure {number} written to {FIG}", flush=True)
        qa = ROOT / "qa"
        qa.mkdir(exist_ok=True)
        if LAYOUT_CHECKS:
            (qa / "figure_layout_checks.json").write_text(json.dumps(LAYOUT_CHECKS, indent=2) + "\n")
        if PLOT_SERIES:
            pd.DataFrame(PLOT_SERIES).to_csv(qa / "figure3_plotted_values.csv", index=False)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Figure generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
