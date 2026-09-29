"""
Simulation-based power and precision for the Epistemic Transfer Effect (ETE)
=============================================================================

Design simulated
----------------
Two between-participant arms (assisted practice vs. comparator practice), n per arm.
Every participant answers k_b baseline items (unassisted) and, after the delay,
k delayed items (unassisted, novel). The delayed item set is common to both arms,
which is the protocol's default.

Data-generating process (logistic GLMM with crossed random intercepts)
    logit P(Y_ij = 1) = beta0 + delta * Cond_i + u_i + v_j
    u_i ~ N(0, sigma_u^2)   participant intercept (correlation rho between sessions)
    v_j ~ N(0, sigma_v^2)   item intercept
    e_ij ~ N(0, sigma_e^2)  participant-by-item deviation (extra-binomial variation)
The condition effect delta is chosen so that the population-averaged accuracy
difference between arms equals the target ETE in percentage points.

Estimator used in the grid
--------------------------
Participant-level: mean delayed accuracy per participant, regressed on arm with
mean baseline accuracy as covariate (ANCOVA). Because both arms answer the same
delayed items, item effects are balanced across arms and this estimator has
close to the same precision as the marginal contrast from the full GLMM
(checked against glmer fits in validate_glmm.R). It is fast enough for a full grid.

Decisions evaluated
-------------------
superiority : two-sided 95% CI excludes 0
equivalence : 90% CI lies within [-SESOI, +SESOI] (TOST at alpha = .05)
halfwidth   : mean half-width of the 95% CI (precision benchmark)

Usage: python sim_power_ete.py  (writes results/ete_power_grid.csv)
"""
import numpy as np
import pandas as pd
from scipy import stats, optimize
from itertools import product
import os, time

rng = np.random.default_rng(20260922)
OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- helpers
GH_X, GH_W = np.polynomial.hermite.hermgauss(40)  # Gauss-Hermite for N(0,1)


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def marginal_p(beta, sigma_tot):
    """Population-averaged P(Y=1) when logit = beta + N(0, sigma_tot^2)."""
    z = np.sqrt(2.0) * sigma_tot * GH_X
    return float(np.sum(GH_W * expit(beta + z)) / np.sqrt(np.pi))


def solve_beta(target_p, sigma_tot):
    return optimize.brentq(lambda b: marginal_p(b, sigma_tot) - target_p, -8, 8)


def one_sim(n, k, ete_pp, sigma_u, sigma_v, k_b=8, p_comp=0.62, sesoi=0.05,
            rho=0.5, sigma_e=1.3):
    """rho: correlation of participant ability between baseline and delayed session;
    sigma_e: participant-by-item (trial-level) deviation on the logit scale."""
    sigma_tot = np.sqrt(sigma_u**2 + sigma_v**2 + sigma_e**2)
    beta0 = solve_beta(p_comp, sigma_tot)
    beta1 = solve_beta(p_comp + ete_pp / 100.0, sigma_tot)
    delta = beta1 - beta0

    N = 2 * n
    cond = np.repeat([0, 1], n)
    u = rng.normal(0, sigma_u, N)                                    # delayed-session ability
    u_b = rho * u + np.sqrt(1 - rho**2) * rng.normal(0, sigma_u, N)  # baseline ability
    v_b = rng.normal(0, sigma_v, k_b)
    v_d = rng.normal(0, sigma_v, k)

    # baseline block (no condition effect)
    lp_b = beta0 + u_b[:, None] + v_b[None, :] + rng.normal(0, sigma_e, (N, k_b))
    y_b = rng.random((N, k_b)) < expit(lp_b)
    base = y_b.mean(axis=1)

    # delayed block
    lp_d = (beta0 + delta * cond[:, None] + u[:, None] + v_d[None, :]
            + rng.normal(0, sigma_e, (N, k)))
    y_d = rng.random((N, k)) < expit(lp_d)
    dela = y_d.mean(axis=1)

    # ANCOVA: dela ~ 1 + cond + base
    X = np.column_stack([np.ones(N), cond, base - base.mean()])
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ dela
    resid = dela - X @ b
    s2 = resid @ resid / (N - 3)
    se = np.sqrt(s2 * XtX_inv[1, 1])
    est = b[1]
    df = N - 3
    t95 = stats.t.ppf(0.975, df)
    t90 = stats.t.ppf(0.95, df)
    lo95, hi95 = est - t95 * se, est + t95 * se
    lo90, hi90 = est - t90 * se, est + t90 * se
    return dict(
        est=est, se=se,
        superior=(lo95 > 0) or (hi95 < 0),
        equivalent=(lo90 > -sesoi) and (hi90 < sesoi),
        halfwidth95=t95 * se,
        delta_logit=delta,
    )


def run_grid(n_list, k_list, ete_list, sigma_u, sigma_v, nsim, tag):
    rows = []
    t0 = time.time()
    for n, k, ete in product(n_list, k_list, ete_list):
        res = [one_sim(n, k, ete, sigma_u, sigma_v) for _ in range(nsim)]
        df = pd.DataFrame(res)
        rows.append(dict(
            grid=tag, sigma_u=sigma_u, sigma_v=sigma_v, n_per_arm=n, k_delayed=k,
            true_ete_pp=ete, nsim=nsim,
            power_superiority=df.superior.mean(),
            power_equivalence=df.equivalent.mean(),
            mean_halfwidth_pp=100 * df.halfwidth95.mean(),
            mean_est_pp=100 * df.est.mean(),
            delta_logit=df.delta_logit.iloc[0],
        ))
        print(f"{tag} n={n:4d} k={k:2d} ete={ete}: sup={df.superior.mean():.2f} "
              f"equiv={df.equivalent.mean():.2f} hw={100*df.halfwidth95.mean():.2f} "
              f"[{time.time()-t0:.0f}s]", flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    NSIM = 1000
    main = run_grid(
        n_list=[150, 250, 400, 600, 800, 1000, 1250],
        k_list=[16, 24, 32],
        ete_list=[0, 3, 5],
        sigma_u=1.2, sigma_v=1.0, nsim=NSIM, tag="main",
    )
    sens = pd.concat([
        run_grid([150, 400, 800], [24], [0, 5], su, 1.0, NSIM, f"sens_su{su}")
        for su in (0.8, 1.6)
    ])
    grid = pd.concat([main, sens], ignore_index=True)
    grid.to_csv(os.path.join(OUT, "ete_power_grid.csv"), index=False)
    print("written", os.path.join(OUT, "ete_power_grid.csv"))
