"""
Item-by-condition heterogeneity and two-way cluster-robust inference for the ETE
================================================================================
Extends sim_power_ete.py. Adds a random slope of condition across items
(sigma_slope on the logit scale), so that the size of the ETE varies from item to
item, and analyses each simulated dataset with a linear probability model on
trial-level accuracy with two-way (participant + item) cluster-robust standard
errors (Cameron, Gelbach & Miller, 2011), using a t critical value with
df = min(participants, items) - 1. The participant-level ANCOVA of
sim_power_ete.py is reported alongside for comparison.
Writes results/ete_heterogeneity_grid.csv
"""
import numpy as np, pandas as pd, os, time
from scipy import stats
from itertools import product
import sim_power_ete as S

rng = np.random.default_rng(31)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")

def twoway_cr(X, y, cl1, cl2):
    """OLS with two-way cluster-robust variance (CR1 small-sample factors)."""
    XtX_inv = np.linalg.inv(X.T @ X); b = XtX_inv @ X.T @ y; e = y - X @ b
    Xe = X * e[:, None]
    def meat(cl):
        G = cl.max() + 1
        S_ = np.zeros((G, X.shape[1])); np.add.at(S_, cl, Xe)
        return (S_.T @ S_) * G / (G - 1)
    V = XtX_inv @ (meat(cl1) + meat(cl2) - Xe.T @ Xe) @ XtX_inv
    return b, np.sqrt(np.maximum(np.diag(V), 0))

def one_sim(n, k, ete_pp, sigma_slope, sigma_u=1.2, sigma_v=1.0, sigma_e=1.3, rho=0.5, k_b=8, p_comp=0.62, sesoi=0.05):
    # comparator arm has no slope contribution; the assisted arm carries the item-varying effect
    sigma_tot0 = np.sqrt(sigma_u**2 + sigma_v**2 + sigma_e**2)
    sigma_tot1 = np.sqrt(sigma_u**2 + sigma_v**2 + sigma_e**2 + sigma_slope**2)
    beta0 = S.solve_beta(p_comp, sigma_tot0); delta = S.solve_beta(p_comp + ete_pp / 100, sigma_tot1) - beta0
    N = 2 * n; cond = np.repeat([0, 1], n)
    u = rng.normal(0, sigma_u, N); u_b = rho * u + np.sqrt(1 - rho**2) * rng.normal(0, sigma_u, N)
    v_b = rng.normal(0, sigma_v, k_b); v_d = rng.normal(0, sigma_v, k); sl = rng.normal(0, sigma_slope, k)
    y_b = rng.random((N, k_b)) < S.expit(beta0 + u_b[:, None] + v_b[None, :] + rng.normal(0, sigma_e, (N, k_b)))
    base = y_b.mean(1)
    lp = beta0 + (delta + sl[None, :]) * cond[:, None] + u[:, None] + v_d[None, :] + rng.normal(0, sigma_e, (N, k))
    y = (rng.random((N, k)) < S.expit(lp)).astype(float)
    # trial-level LPM with two-way CR
    yy = y.ravel(); cc = np.repeat(cond, k).astype(float); bb = np.repeat(base - base.mean(), k)
    X = np.column_stack([np.ones(N * k), cc, bb]); pid = np.repeat(np.arange(N), k); iid = np.tile(np.arange(k), N)
    b, se = twoway_cr(X, yy, pid, iid); df = min(N, k) - 1
    t95, t90 = stats.t.ppf(0.975, df), stats.t.ppf(0.95, df)
    est, s = b[1], se[1]
    # participant-level ANCOVA
    dela = y.mean(1); Xp = np.column_stack([np.ones(N), cond, base - base.mean()])
    XtX = np.linalg.inv(Xp.T @ Xp); bp = XtX @ Xp.T @ dela; r = dela - Xp @ bp
    sp = np.sqrt(r @ r / (N - 3) * XtX[1, 1]); tp = stats.t.ppf(0.975, N - 3)
    return dict(cr_est=est, cr_hw=t95 * s, cr_sup=abs(est) > t95 * s, cr_equiv=(est - t90 * s > -sesoi) and (est + t90 * s < sesoi),
                cr_cover=abs(est - ete_pp / 100) <= t95 * s, pl_hw=tp * sp, pl_cover=abs(bp[1] - ete_pp / 100) <= tp * sp)

if __name__ == "__main__":
    rows = []; t0 = time.time(); NSIM = 1000
    for slope, n, k, ete in product([0.0, 0.3], [150, 250, 400, 600], [16, 24, 32], [0, 5]):
        if slope == 0.0 and k != 24: continue
        r = pd.DataFrame([one_sim(n, k, ete, slope) for _ in range(NSIM)])
        rows.append(dict(sigma_slope=slope, n_per_arm=n, k_delayed=k, true_ete_pp=ete, nsim=NSIM,
                         cr_power_superiority=r.cr_sup.mean(), cr_power_equivalence=r.cr_equiv.mean(),
                         cr_halfwidth_pp=100 * r.cr_hw.mean(), cr_coverage=r.cr_cover.mean(),
                         pl_halfwidth_pp=100 * r.pl_hw.mean(), pl_coverage=r.pl_cover.mean()))
        print(rows[-1], f"[{time.time()-t0:.0f}s]", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "ete_heterogeneity_grid.csv"), index=False); print("written")
