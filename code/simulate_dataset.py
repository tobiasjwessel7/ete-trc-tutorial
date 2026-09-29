"""
Simulated two-wave dataset for the worked example
=================================================
Four practice arms x n participants, five phases, known population truths.
The data-generating process is the crossed-random-effects logistic model of
sim_power_ete.py, with the same calibrated variance components:
    sigma_u = 1.2 (participant), sigma_v = 1.0 (item), sigma_e = 1.3 (participant x item),
    baseline-delayed ability correlation rho = 0.5.

Phases and items
    baseline  : 8 unassisted items, all arms
    probe     : 8 novel items immediately after practice. In the two AI arms the
                tool is available on a random half of the items (randomised per
                participant, order randomised); the two non-AI arms answer the
                same 8 items unassisted (matched probe block).
    delayed   : 24 novel unassisted items, 8 each at near / intermediate / far
                transfer distance, common to all arms.

Population truths (percentage points of accuracy, averaged over the population)
    active practice (comparator) delayed accuracy: 62 (near), 58 (intermediate), 54 (far)
    ETE vs. active practice:  answer-first AI -4,  evidence-first AI +1,  no-practice -6
    unassisted probe accuracy: 62;  with-tool probe accuracy: 92 (answer-first), 96 (evidence-first)
    => TRC = 30 pp (answer-first), 34 pp (evidence-first)
Writes data/simulated_two_wave.csv (long format, one row per trial).
"""
import numpy as np, pandas as pd, os
from scipy import optimize

rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data"); os.makedirs(OUT, exist_ok=True)

SU, SV, SE, RHO = 1.2, 1.0, 1.3, 0.5
N_PER_ARM = 300
ARMS = ["answer_first_ai", "evidence_first_ai", "active_practice", "no_practice"]
GH_X, GH_W = np.polynomial.hermite.hermgauss(40)

def expit(x): return 1 / (1 + np.exp(-x))
def marginal_p(beta, s):
    return float(np.sum(GH_W * expit(beta + np.sqrt(2) * s * GH_X)) / np.sqrt(np.pi))
def beta_for(p, s): return optimize.brentq(lambda b: marginal_p(b, s) - p, -8, 8)

S_TOT = np.sqrt(SU**2 + SV**2 + SE**2)
N = N_PER_ARM * len(ARMS)
arm = np.repeat(ARMS, N_PER_ARM)
pid = np.arange(1, N + 1)
u = rng.normal(0, SU, N)
u_b = RHO * u + np.sqrt(1 - RHO**2) * rng.normal(0, SU, N)

rows = []
def add_block(phase, items, lp, avail=None, distance=None):
    y = (rng.random(lp.shape) < expit(lp)).astype(int)
    for i in range(N):
        order = rng.permutation(len(items))
        for pos, j in enumerate(order):
            rows.append(dict(participant=pid[i], arm=arm[i], phase=phase, item=items[j],
                             position=pos + 1,
                             distance=(distance[j] if distance is not None else ""),
                             tool_available=(int(avail[i, j]) if avail is not None else 0),
                             correct=int(y[i, j])))

# ---- baseline
items_b = [f"B{j+1:02d}" for j in range(8)]
v_b = rng.normal(0, SV, 8)
lp_b = beta_for(0.62, S_TOT) + u_b[:, None] + v_b[None, :] + rng.normal(0, SE, (N, 8))
add_block("baseline", items_b, lp_b)

# ---- immediate probe (TRC)
items_p = [f"P{j+1:02d}" for j in range(8)]
v_p = rng.normal(0, SV, 8)
avail = np.zeros((N, 8), dtype=int)
b_off = beta_for(0.62, S_TOT)
tau = {"answer_first_ai": beta_for(0.92, np.sqrt(S_TOT**2 + 0.5**2)) - b_off,
       "evidence_first_ai": beta_for(0.96, np.sqrt(S_TOT**2 + 0.5**2)) - b_off}
slope = rng.normal(0, 0.5, N)          # participant-specific reliance on the tool
lp_p = b_off + u[:, None] + v_p[None, :] + rng.normal(0, SE, (N, 8))
for i in range(N):
    if arm[i] in tau:
        on = rng.permutation(8)[:4]
        avail[i, on] = 1
        lp_p[i, on] += tau[arm[i]] + slope[i]
add_block("probe", items_p, lp_p, avail=avail)

# ---- delayed unassisted test (ETE)
dist = np.repeat(["near", "intermediate", "far"], 8)
items_d = [f"D{j+1:02d}" for j in range(24)]
v_d = rng.normal(0, SV, 24)
p_comp = {"near": 0.62, "intermediate": 0.58, "far": 0.54}
ete = {"answer_first_ai": -0.04, "evidence_first_ai": 0.01, "active_practice": 0.0, "no_practice": -0.06}
lp_d = np.zeros((N, 24))
for j in range(24):
    for i in range(N):
        lp_d[i, j] = beta_for(p_comp[dist[j]] + ete[arm[i]], S_TOT)
lp_d += u[:, None] + v_d[None, :] + rng.normal(0, SE, (N, 24))
add_block("delayed", items_d, lp_d, distance=dist)

df = pd.DataFrame(rows)
base_mean = df[df.phase == "baseline"].groupby("participant").correct.mean().rename("baseline_mean")
df = df.merge(base_mean, on="participant")
df.to_csv(os.path.join(OUT, "simulated_two_wave.csv"), index=False)
print(df.shape, df.groupby(["arm", "phase"]).correct.mean().round(3).unstack())
