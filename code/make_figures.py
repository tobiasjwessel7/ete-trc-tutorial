"""Figures for the manuscript, drawn with matplotlib in a consistent house style.
Run after sim_power_ete.py, validate_glmm.R and estimate_ete_trc.R.
Outputs PNG (300 dpi) and PDF into ../figures/.
"""
import os, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results"); FIG = os.path.join(HERE, "..", "figures"); os.makedirs(FIG, exist_ok=True)

NAVY, TEAL, ORANGE, GREEN, GREY = "#1F3B5C", "#1B8A8A", "#E07B22", "#3E8E41", "#7A7F87"
NAVY_L, TEAL_L, ORANGE_L, GREEN_L, GREY_L = "#DCE4EE", "#D5EDED", "#FBE6D3", "#DDEEDD", "#ECEDEF"
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
MM = 1 / 25.4


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(os.path.join(FIG, name + ".pdf"), bbox_inches="tight", facecolor="white")
    fig.savefig(os.path.join(FIG, name + ".tiff"), dpi=600, bbox_inches="tight", facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


def box(ax, x, y, w, h, text, fc, ec, tc="black", fs=8, bold=False, r=0.02, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, color=GREY, ls="-", lw=1.1, ms=8):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=ms, color=color,
                                 linestyle=ls, lw=lw, shrinkA=0, shrinkB=0))


# ------------------------------------------------------------------ Figure 1: two questions, two estimands
def figure1():
    fig, ax = plt.subplots(figsize=(170 * MM, 72 * MM))
    ax.set_xlim(0, 100); ax.set_ylim(0, 44); ax.axis("off")
    ax.plot([2, 98], [37, 37], color=GREY, lw=1.2, zorder=1)
    stages = [(2, 21, "Practice\nwith the tool", NAVY), (28, 22, "Immediate probe\n(novel items)", NAVY),
              (53, 17, "Delay\n(days to weeks)", GREY), (74, 24, "Delayed test\n(novel items, no tool)", NAVY)]
    for x, w, t, c in stages:
        box(ax, x, 32.5, w, 9, t, fc="white", ec=c, tc=c, fs=6.8, bold=True, r=1.2)
    cx_t, cx_e = 39, 86.5
    ax.text(cx_t, 27.5, "What does the tool add right now?", ha="center", va="center", fontsize=7.6, color=ORANGE, fontweight="bold")
    ax.text(cx_e, 27.5, "What does the user keep without it?", ha="center", va="center", fontsize=7.6, color=GREEN, fontweight="bold")
    arrow(ax, cx_t, 32.5, cx_t, 29.5, color=ORANGE, ls="--", ms=7)
    arrow(ax, cx_e, 32.5, cx_e, 29.5, color=GREEN, ls="--", ms=7)
    box(ax, cx_t - 12.5, 17, 12, 7, "with\ntool", fc=ORANGE_L, ec=ORANGE, fs=6.5, r=1)
    box(ax, cx_t + 0.5, 17, 12, 7, "without\ntool", fc="white", ec=ORANGE, fs=6.5, r=1)
    box(ax, cx_e - 12.5, 17, 12, 7, "assisted\npractice", fc=GREEN_L, ec=GREEN, fs=6.5, r=1)
    box(ax, cx_e + 0.5, 17, 12, 7, "comparator\npractice", fc="white", ec=GREEN, fs=6.5, r=1)
    ax.text(cx_t, 14, "TRC: accuracy with minus without,\nsame people, same moment", ha="center", va="top", fontsize=6.4, color=ORANGE, linespacing=1.25)
    ax.text(cx_e, 14, "ETE: later unassisted accuracy after assisted\nversus comparator practice", ha="center", va="top", fontsize=6.4, color=GREEN, linespacing=1.25)
    ax.text(50, 3, "Neither quantity identifies the other: a large tool advantage is compatible with strong, absent, or negative retained capability.",
            ha="center", va="center", fontsize=6.4, color=NAVY, style="italic")
    save(fig, "fig1_two_estimands")


# ------------------------------------------------------------------ Figure 2: protocol
def figure2():
    fig, ax = plt.subplots(figsize=(170 * MM, 96 * MM))
    ax.set_xlim(0, 101); ax.set_ylim(0, 60); ax.axis("off")
    phases = [("1  Baseline", "unassisted items;\naccuracy, confidence,\ncovariates"),
              ("2  Random\n    assignment", "one of four\npractice regimes"),
              ("3  Practice", "enough trials or\nsessions for learning\nto be possible"),
              ("4  Immediate\n    probe", "novel items; tool on\na random half (AI);\nmatched block (others)"),
              ("5  Delayed test", "7–14 days later;\nnovel items only;\nnear / mid / far;\nno tool")]
    w, gap = 18.6, 1.75; xs = [1 + i * (w + gap) for i in range(5)]
    for i, (x, (t, s)) in enumerate(zip(xs, phases)):
        box(ax, x, 43, w, 16.5, "", fc="white", ec=NAVY, r=1.2, lw=1.2)
        ax.text(x + 1.0, 58.4, t, ha="left", va="top", fontsize=6.6, color=NAVY, fontweight="bold", linespacing=1.15)
        ax.text(x + 1.0, 52.0, s, ha="left", va="top", fontsize=5.6, color="black", linespacing=1.25)
        if i < 4:
            arrow(ax, x + w, 51.5, xs[i + 1], 51.5, color=GREY, ms=6)
    # estimand callouts under phase 4 and 5
    cx4, cx5 = xs[3] + w / 2, xs[4] + w / 2
    arrow(ax, cx4, 43, cx4, 40.5, color=ORANGE, ls="--", ms=6)
    box(ax, xs[3], 31, w, 9.5, "", fc=ORANGE_L, ec=ORANGE, r=1.2, lw=1.1)
    ax.text(cx4, 38.6, "TRC", ha="center", va="top", fontsize=7.4, color=ORANGE, fontweight="bold")
    ax.text(cx4, 35.4, "with vs. without tool,\nwithin person, at probe", ha="center", va="top", fontsize=5.6, linespacing=1.2)
    arrow(ax, cx5, 43, cx5, 40.5, color=GREEN, ls="--", ms=6)
    box(ax, xs[4], 31, w, 9.5, "", fc=GREEN_L, ec=GREEN, r=1.2, lw=1.1)
    ax.text(cx5, 38.6, "ETE", ha="center", va="top", fontsize=7.4, color=GREEN, fontweight="bold")
    ax.text(cx5, 35.4, "AI arm vs. C and D,\nbetween arms, delayed", ha="center", va="top", fontsize=5.6, linespacing=1.2)
    # branch to arms
    cx2 = xs[1] + w / 2
    arms = [("A  Answer-first AI", "verdict shown before\nthe user judges", ORANGE, ORANGE_L),
            ("B  Evidence-first AI", "evidence work before\nthe verdict", TEAL, TEAL_L),
            ("C  Active practice", "the same work,\nwithout AI", GREEN, GREEN_L),
            ("D  No practice", "matched-duration\nunrelated activity", GREY, GREY_L)]
    aw, agap = 18.6, 1.75; ax_x = [1 + i * (aw + agap) for i in range(4)]
    ax.plot([cx2, cx2], [43, 26], color=GREY, lw=1.1)
    ax.plot([ax_x[0] + aw / 2, ax_x[3] + aw / 2], [26, 26], color=GREY, lw=1.1)
    for x, (t, s, c, cl) in zip(ax_x, arms):
        arrow(ax, x + aw / 2, 26, x + aw / 2, 22.5, color=GREY, ms=6)
        box(ax, x, 12, aw, 10.5, "", fc=cl, ec=c, r=1.2, lw=1.1)
        ax.text(x + aw / 2, 20.8, t, ha="center", va="top", fontsize=6.1, color=c, fontweight="bold")
        ax.text(x + aw / 2, 17.4, s, ha="center", va="top", fontsize=5.6, color="black", linespacing=1.2)
    ax.text(1, 8.3, "Reported with every ETE: comparator (C and D), delay, access regime at test, item novelty, transfer distance,\n"
                    "dose, smallest effect of interest, equivalence decision.", ha="left", va="top", fontsize=6.2, color=NAVY, linespacing=1.3)
    ax.text(1, 2.2, "Before analysis: audit the implementation against the protocol (availability, item sets, orders randomised as specified).",
            ha="left", va="center", fontsize=6.2, color=NAVY, style="italic")
    save(fig, "fig2_protocol")


# ------------------------------------------------------------------ Figure 3: power and precision
def figure3():
    g = pd.read_csv(os.path.join(RES, "ete_power_grid.csv"))
    m = g[g.grid == "main"]
    has_trc = os.path.exists(os.path.join(RES, "validation_trc.csv"))
    ncol = 3 if has_trc else 2
    fig, axes = plt.subplots(1, ncol, figsize=(170 * MM, 66 * MM))
    # A: power
    ax = axes[0]
    for ete, c, lab in [(5, NAVY, "true ETE = 5 pp"), (3, TEAL, "true ETE = 3 pp")]:
        s = m[(m.k_delayed == 24) & (m.true_ete_pp == ete)]
        ax.plot(s.n_per_arm, s.power_superiority, marker="o", ms=3.5, color=c, label=lab)
    s = m[(m.k_delayed == 24) & (m.true_ete_pp == 0)]
    ax.plot(s.n_per_arm, s.power_equivalence, marker="s", ms=3.5, color=GREEN, label="equivalence, true ETE = 0")
    ax.axhline(0.8, color=GREY, lw=0.8, ls=":")
    ax.set_xlabel("Participants per arm"); ax.set_ylabel("Power")
    ax.set_ylim(0, 1.02); ax.set_title("A  Power, 24 delayed items", loc="left", color=NAVY)
    ax.legend(frameon=False, loc="lower right", fontsize=6.2)
    # B: precision
    ax = axes[1]
    for k, c in [(16, ORANGE), (24, NAVY), (32, TEAL)]:
        s = m[(m.k_delayed == k) & (m.true_ete_pp == 0)]
        ax.plot(s.n_per_arm, s.mean_halfwidth_pp, marker="o", ms=3.5, color=c, label=f"{k} items")
    s = g[(g.grid == "sens_su1.6") & (g.true_ete_pp == 0)]
    ax.plot(s.n_per_arm, s.mean_halfwidth_pp, marker="o", ms=3.5, color=NAVY, ls="--", label="24 items, σu = 1.6")
    hp = os.path.join(RES, "ete_heterogeneity_grid.csv")
    if os.path.exists(hp):
        h = pd.read_csv(hp); h = h[(h.sigma_slope == 0.3) & (h.true_ete_pp == 0)]
        for k, c in [(16, ORANGE), (32, TEAL)]:
            hh = h[h.k_delayed == k]
            ax.plot(hh.n_per_arm, hh.cr_halfwidth_pp, marker="^", ms=3.5, color=c, ls=":", label=f"{k} items, item-varying effect")
    ax.axhline(5, color=GREY, lw=0.8, ls=":"); ax.text(1250, 5.12, "SESOI", ha="right", va="bottom", fontsize=6, color=GREY)
    ax.set_xlabel("Participants per arm"); ax.set_ylabel("95% CI half-width (pp)")
    ax.set_ylim(0, 6.5); ax.set_title("B  Precision of the ETE", loc="left", color=NAVY)
    ax.legend(frameon=False, loc="upper right", fontsize=6.2)
    # C: TRC precision vs probe items
    if has_trc:
        gp = os.path.join(RES, "validation_trc_grid.csv")
        if os.path.exists(gp):   # larger run (150 replications per cell) takes precedence
            a = pd.read_csv(gp); a = a[a.n == 300].rename(columns={"glmm_halfwidth_pp": "glmm_hw", "paired_halfwidth_pp": "paired_hw"})
        else:
            t = pd.read_csv(os.path.join(RES, "validation_trc.csv"))
            a = t.groupby("probe_items")[["glmm_hw", "paired_hw"]].mean().reset_index()
        ax = axes[2]
        ax.plot(a.probe_items, a.glmm_hw, marker="o", ms=3.5, color=ORANGE, label="items as random sample")
        ax.plot(a.probe_items, a.paired_hw, marker="s", ms=3.5, color=GREY, label="items ignored")
        ax.set_xlabel("Probe items (n = 300)"); ax.set_ylabel("95% CI half-width (pp)")
        ax.set_xticks([8, 16, 32]); ax.set_ylim(0, max(6, a.glmm_hw.max() * 1.15))
        ax.set_title("C  Precision of the TRC", loc="left", color=NAVY); ax.legend(frameon=False, loc="upper right", fontsize=6.2)
    fig.tight_layout(w_pad=2.0)
    save(fig, "fig3_power_precision")


# ------------------------------------------------------------------ Figure 4: diagnostic space
def figure4():
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
    save(fig, "fig4_diagnostic_space")


if __name__ == "__main__":
    figure1(); figure2(); figure3(); figure4()
    print("figures written to", FIG)
