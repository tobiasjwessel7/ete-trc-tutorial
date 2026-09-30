# ete-trc-tutorial — code, simulated data and materials

Companion repository for a tutorial manuscript prepared for submission to Behavior Research Methods. Contains only simulation code, simulated data, results and materials; no participant data.

Code, results and figures for: Trattner, C. "What the tool adds and what the user keeps:
Two estimands, a two-wave protocol, and simulation-based power for evaluating AI assistance"
(draft for Behavior Research Methods).

## Layout
- code/sim_power_ete.py      simulation-based power/precision grid for the ETE (Python; fast participant-level estimator)
- code/sim_power_heterogeneity.py  item-varying arm effects with two-way cluster-robust inference (Python)
- code/validate_glmm.R       validation of the fast estimator against glmer contrasts; TRC precision vs. probe items (R, lme4)
- code/simulate_dataset.py   generates the worked-example dataset with known truths (data/simulated_two_wave.csv)
- code/estimate_ete_trc.R    estimation recipe: GLMM, population-averaged contrasts (pp), TOST equivalence, checks
- code/make_figures.py       house-style figures (figures/)
- code/validate_trc_grid.R   TRC precision/coverage with 150 replications per cell at n = 300 (the run used in the paper, ~45 min); larger N x items grid optional
- results/                   ete_power_grid.csv, ete_heterogeneity_grid.csv, validation_ete.csv, validation_trc.csv,
                             validation_trc_grid.csv (150 replications, used in the paper), worked_example_results.csv
- materials/                 protocol_template.md (preregistration-ready), reporting_checklist.md
- figures/                   PNG 300 dpi, PDF, TIFF 600 dpi (LZW) for each figure

## Reproduce
    cd code
    python3 sim_power_ete.py          # ~2 min
    python3 sim_power_heterogeneity.py # ~3 min
    Rscript validate_glmm.R           # ~20-30 min (100 glmer fits)
    Rscript validate_trc_grid.R 150 "300" "8,16,32"  # paper grid, ~30-45 min
    python3 simulate_dataset.py
    Rscript estimate_ete_trc.R ../data/simulated_two_wave.csv 5
    python3 make_figures.py

Requirements: Python 3.11+ with the packages in requirements.txt (pip install -r requirements.txt); R 4.3 with lme4 1.1-35 (the only R package needed).
The results in results/ were produced with Python 3.12, numpy 2.x, R 4.3.3 and lme4 1.1-35.1.
TRC precision with more replications (used in the paper, n = 300):  Rscript validate_trc_grid.R 150 "300" "8,16,32"   (~30-45 min)
Larger grid, optional:  Rscript validate_trc_grid.R 200 "150,300,600" "8,16,32"   (1-3 h)
Data-generating parameters (sigma_u = 1.2, sigma_v = 1.0, sigma_e = 1.3, rho = 0.5, p_comparator = .62)
are arguments of one_sim() in sim_power_ete.py and constants at the top of validate_glmm.R; replace with pilot estimates.

## Figure revision — 29 September 2026

This is a presentation-only revision responding to the figure readability review.
Figures 1–3 have been redrawn from the same definitions, protocol and stored result
CSVs. The supplied Figure 4 files are unchanged. No simulation, estimation or
validation script, source dataset, result CSV, protocol material or licence was changed.

To regenerate **only the corrected figures**, from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 code/make_figures.py --figures 1 2 3
```

`pypdf` is the one additional Python dependency. It assembles the three independently
drawn Figure 3 panels into a single vector PDF; the raster versions are assembled
without resampling. This does not require rerunning the simulations or R analyses.
Omit `--figures 1 2 3` to regenerate all four figures from the available result CSVs.

Figures 1–3 are exported at **170 mm width**, with 8-point body/axis/legend text
and 8.5-point bold headings. Do not shrink them back to the old Figure 3 height.
Figure 3 is now 170 × 192 mm, with panels A, B and C arranged vertically and legends
outside the data areas. All original data series are retained. Its individual panels
are also available in `figures/panels/` as PDF, PNG and TIFF.

`qa/figure_layout_checks.json` records the automated text-boundary and legend-position
checks from the most recent figure generation. `qa/figure3_plotted_values.csv` lists
every plotted data point and its source CSV. `qa/figure_revision_checks.json` documents
the delivered revision's checks, including original-file integrity and the scope of
execution. See `FIGURE_REVISION_NOTES.md` for the feedback-to-change mapping.
