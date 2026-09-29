## =====================================================================
##  validate_glmm.R
##  (A) Does the participant-level ANCOVA used in the power grid
##      (sim_power_ete.py) reproduce the precision of the population-averaged
##      GLMM contrast when the delayed item set is common to all arms?
##  (B) How does the precision of the TRC depend on the number of probe items
##      when items are treated as a random sample (GLMM) versus ignored
##      (within-person paired analysis)?
##  Requires lme4. Writes results/validation_ete.csv and results/validation_trc.csv
## =====================================================================
suppressMessages(library(lme4))
outdir <- file.path("..", "results"); dir.create(outdir, showWarnings = FALSE)
set.seed(20260922)

## ---- helpers (same as estimate_ete_trc.R) --------------------------------
gauss_hermite <- function(m = 40) { i <- seq_len(m - 1); J <- matrix(0, m, m)
  J[cbind(i, i + 1)] <- sqrt(i); J[cbind(i + 1, i)] <- sqrt(i)
  e <- eigen(J, symmetric = TRUE); list(x = e$values, w = e$vectors[1, ]^2) }
GH <- gauss_hermite(40)
pa_prob <- function(eta, s) vapply(eta, function(e) sum(GH$w * plogis(e + s * GH$x)), numeric(1))
re_sd <- function(model, avail = 0) { vc <- VarCorr(model); v <- 0
  for (g in names(vc)) { M <- as.matrix(vc[[g]]); nm <- rownames(M)
    if (length(nm) == 1) v <- v + M[1, 1] else { a <- c(1, avail)[seq_along(nm)]; v <- v + as.numeric(t(a) %*% M %*% a) } }
  sqrt(v) }
pa_contrast <- function(model, nd_a, nd_b, avail_a = 0, avail_b = 0, R = 2000) {
  b <- fixef(model); V <- as.matrix(vcov(model))
  draws <- t(b + t(chol(V)) %*% matrix(rnorm(R * length(b)), length(b), R))
  f <- delete.response(terms(model, fixed.only = TRUE))
  Xa <- model.matrix(f, nd_a); Xb <- model.matrix(f, nd_b)
  sa <- re_sd(model, avail_a); sb <- re_sd(model, avail_b)
  diff <- apply(draws, 1, function(bb) mean(pa_prob(Xa %*% bb, sa)) - mean(pa_prob(Xb %*% bb, sb)))
  c(estimate = mean(diff), lo = unname(quantile(diff, .025)), hi = unname(quantile(diff, .975))) }
beta_for <- function(p, s) uniroot(function(b) sum(GH$w * plogis(b + s * GH$x)) - p, c(-8, 8))$root

## ---- data-generating process (mirrors sim_power_ete.py) -------------------
SU <- 1.2; SV <- 1.0; SE <- 1.3; RHO <- 0.5; PC <- 0.62; KB <- 8
STOT <- sqrt(SU^2 + SV^2 + SE^2)

gen_ete <- function(n, k, ete_pp) {
  N <- 2 * n; cond <- rep(0:1, each = n)
  u <- rnorm(N, 0, SU); ub <- RHO * u + sqrt(1 - RHO^2) * rnorm(N, 0, SU)
  b0 <- beta_for(PC, STOT); delta <- beta_for(PC + ete_pp / 100, STOT) - b0
  vb <- rnorm(KB, 0, SV); vd <- rnorm(k, 0, SV)
  yb <- matrix(rbinom(N * KB, 1, plogis(b0 + ub + rep(vb, each = N) + rnorm(N * KB, 0, SE))), N, KB)
  yd <- matrix(rbinom(N * k, 1, plogis(b0 + delta * cond + u + rep(vd, each = N) + rnorm(N * k, 0, SE))), N, k)
  base <- rowMeans(yb)
  data.frame(participant = factor(rep(1:N, k)), cond = rep(cond, k), item = factor(rep(1:k, each = N)),
             correct = as.vector(yd), baseline_c = rep(base - mean(base), k))
}

gen_trc <- function(n, m, trc_target = 0.30, slope_sd = 0.5) {
  u <- rnorm(n, 0, SU); sl <- rnorm(n, 0, slope_sd); v <- rnorm(m, 0, SV)
  b0 <- beta_for(PC, STOT); tau <- beta_for(PC + trc_target, sqrt(STOT^2 + slope_sd^2)) - b0
  avail <- t(sapply(1:n, function(i) { a <- rep(0, m); a[sample(m, m / 2)] <- 1; a }))
  eta <- b0 + u + tau * avail + sl * avail + rep(v, each = n) + rnorm(n * m, 0, SE)
  data.frame(participant = factor(rep(1:n, m)), item = factor(rep(1:m, each = n)),
             avail = as.vector(avail), correct = rbinom(n * m, 1, plogis(as.vector(eta))))
}

## ---- (A) ETE: fast estimator vs GLMM --------------------------------------
NSIM <- 20
ete_rows <- list()
for (cell in list(c(150, 16), c(300, 24))) {
  n <- cell[1]; k <- cell[2]
  for (s in 1:NSIM) {
    dd <- gen_ete(n, k, 0)
    m <- glmer(correct ~ cond + baseline_c + (1 | participant) + (1 | item), data = dd, family = binomial,
               control = glmerControl(optimizer = "bobyqa"))
    ndf <- function(cnd) data.frame(cond = cnd, baseline_c = 0)
    g <- pa_contrast(m, ndf(1), ndf(0))
    pl <- aggregate(correct ~ participant + cond + baseline_c, data = dd, FUN = mean)
    f <- lm(correct ~ cond + baseline_c, data = pl); ci <- confint(f)["cond", ]
    ete_rows[[length(ete_rows) + 1]] <- data.frame(n_per_arm = n, k_delayed = k, sim = s,
      glmm_est = g["estimate"] * 100, glmm_hw = (g["hi"] - g["lo"]) / 2 * 100,
      fast_est = coef(f)["cond"] * 100, fast_hw = diff(ci) / 2 * 100)
    cat(sprintf("A n=%d k=%d sim=%d glmm_hw=%.2f fast_hw=%.2f\n", n, k, s,
                (g["hi"] - g["lo"]) / 2 * 100, diff(ci) / 2 * 100)); flush.console()
  }
}
ete_tab <- do.call(rbind, ete_rows)
write.csv(ete_tab, file.path(outdir, "validation_ete.csv"), row.names = FALSE)
print(aggregate(cbind(glmm_hw, fast_hw, glmm_est, fast_est) ~ n_per_arm + k_delayed, data = ete_tab, FUN = mean))

## ---- (B) TRC precision vs number of probe items ---------------------------
trc_rows <- list()
for (m_items in c(8, 16, 32)) for (s in 1:NSIM) {
  dd <- gen_trc(300, m_items)
  mod <- glmer(correct ~ avail + (1 + avail | participant) + (1 | item), data = dd, family = binomial,
               control = glmerControl(optimizer = "bobyqa"))
  g <- pa_contrast(mod, data.frame(avail = 1), data.frame(avail = 0), avail_a = 1, avail_b = 0)
  wp <- aggregate(correct ~ participant + avail, data = dd, FUN = mean)
  dif <- wp$correct[wp$avail == 1] - wp$correct[wp$avail == 0]; tt <- t.test(dif)
  trc_rows[[length(trc_rows) + 1]] <- data.frame(n = 300, probe_items = m_items, sim = s,
    glmm_est = g["estimate"] * 100, glmm_hw = (g["hi"] - g["lo"]) / 2 * 100,
    paired_est = mean(dif) * 100, paired_hw = diff(tt$conf.int) / 2 * 100)
  cat(sprintf("B m=%d sim=%d glmm_hw=%.2f paired_hw=%.2f\n", m_items, s, (g["hi"] - g["lo"]) / 2 * 100, diff(tt$conf.int) / 2 * 100)); flush.console()
}
trc_tab <- do.call(rbind, trc_rows)
write.csv(trc_tab, file.path(outdir, "validation_trc.csv"), row.names = FALSE)
print(aggregate(cbind(glmm_hw, paired_hw, glmm_est, paired_est) ~ probe_items, data = trc_tab, FUN = mean))
cat("done\n")
