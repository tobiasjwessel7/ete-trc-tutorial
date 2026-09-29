# Protocol template — two-wave study of retained capability after AI assistance

Fill every field before data collection and register the completed document publicly (for example on OSF).
Bracketed text is a placeholder. The numbering follows the tutorial (Trattner, 2026, Behavior Research Methods).

## 1. Estimands
- Primary: Epistemic Transfer Effect (ETE) = difference in delayed unassisted accuracy (percentage points) between
  [assisted arm(s)] and (a) active practice, (b) no practice, on novel items, at [delay].
- Secondary: Tool-Removal Cost (TRC) = within-person difference in accuracy with vs. without the tool on the
  immediate probe, per assisted arm.
- Smallest effect size of interest (SESOI) for the ETE: [±X] points. Equivalence bounds: [−X, +X].
- Assessment regime at the delayed test: [no tool / fixed evidence packet / open search] — no functionally equivalent aid.

## 2. Arms (between participants)
- A [assisted arm 1: what the participant sees and must do]
- B [assisted arm 2, optional]
- C Active practice: same work on comparable items, no AI, [reference answer shown? when?]
- D No practice: [unrelated activity], matched for duration [minutes].
Allocation: [simple randomisation / balanced within recruitment batches]; allocation ratio [1:1:1:1].

## 3. Items
- Pool: [N] items, domains [..], truth status [true/false/misleading], reference judgments documented in [file].
- Sets: baseline [n_b], practice [n_p], probe [n_probe], delayed [n_d = near/intermediate/far: .. / .. / ..].
- Matching across sets on: domain, truth status, familiarity, reading difficulty, estimated difficulty [method].
- Novelty check: [textual overlap threshold], [semantic similarity threshold], human review by [who].
- Mixed-truth items scored as a separate stratum: [yes/no].

## 4. Phases
1. Baseline: [n_b] items, unassisted; response + confidence [0–100]; covariates [list].
2. Random assignment.
3. Practice: [n_p] trials / [sessions]; expected within-session improvement in arm C used as dose check.
4. Immediate probe: [n_probe] novel items; in assisted arms tool available on a random half, availability-to-item
   assignment and order randomised per participant; arms C and D answer the same items unassisted.
5. Delayed test: [delay, e.g. 7–14 days; window]; [n_d] novel items; unassisted; second follow-up at [weeks] (optional).
6. Debriefing with corrections after the last measurement.

## 5. Sample
- Target population: [..]. Recruitment: [platform]. Eligibility: [..].
- Planned delayed completers per arm: [n], from simulation with participant SD [σu], item SD [σv],
  participant×item SD [σe], session correlation [ρ], comparator accuracy [p], [items] delayed items
  (script: sim_power_ete.py; item-varying effects: sim_power_heterogeneity.py). Attrition budget: [%].
- Exclusions (fixed in advance): [consent, duplicates, no usable data, attention check policy, speed threshold].

## 6. Analysis
- ETE model: logit P(correct) = arm + distance + baseline + (1 | participant) + (1 | item) [+ arm×distance];
  contrasts reported as population-averaged differences in percentage points with 95% and 90% intervals.
- Decision rules: different from zero if the 95% interval excludes 0; equivalent if the 90% interval lies within
  [−X, +X]; otherwise inconclusive. Report all four outcomes as such.
- Checks: participant-level ANCOVA; two-way (participant + item) cluster-robust linear probability model.
- TRC model: logit P(correct) = availability × arm + position + (1 + availability | participant) + (1 | item);
  population-averaged TRC per arm; within-person paired check reported with the item-sampling caveat.
- Sensitivity: availability-by-order; exclusions; delay window.

## 7. Implementation audit (before any model is fitted)
- Tabulate tool availability by probe position and arm; confirm randomisation.
- Confirm item-order randomisation per participant and arm balance within batches.
- Record any deviation and its consequences for identification here: [..].

## 8. Deviations from this protocol
[Record after data collection; leave empty before.]
