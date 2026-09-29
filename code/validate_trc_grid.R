## =====================================================================
##  validate_trc_grid.R — precision and coverage of the TRC across an
##  N x probe-items grid, with more replications than validate_glmm.R.
##  Usage: Rscript validate_trc_grid.R [nsim] [n values] [item values]
##  e.g.   Rscript validate_trc_grid.R 200 "150,300,600" "8,16,32"   (~1-3 h)
##  Writes results/validation_trc_grid.csv (one row per cell). Requires lme4.
## =====================================================================
suppressMessages(library(lme4))
args <- commandArgs(trailingOnly = TRUE)
NSIM  <- if (length(args) >= 1) as.integer(args[1]) else 200
NS    <- if (length(args) >= 2) as.integer(strsplit(args[2], ",")[[1]]) else c(150, 300, 600)
MS    <- if (length(args) >= 3) as.integer(strsplit(args[3], ",")[[1]]) else c(8, 16, 32)
outdir <- file.path("..", "results"); dir.create(outdir, showWarnings = FALSE); set.seed(2027)
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
SU <- 1.2; SV <- 1.0; SE <- 1.3; PC <- 0.62; STOT <- sqrt(SU^2 + SV^2 + SE^2)
gen_trc <- function(n, m, trc_target = 0.30, slope_sd = 0.5) {
  u <- rnorm(n, 0, SU); sl <- rnorm(n, 0, slope_sd); v <- rnorm(m, 0, SV)
  b0 <- beta_for(PC, STOT); tau <- beta_for(PC + trc_target, sqrt(STOT^2 + slope_sd^2)) - b0
  avail <- t(sapply(1:n, function(i) { a <- rep(0, m); a[sample(m, m / 2)] <- 1; a }))
  eta <- b0 + u + tau * avail + sl * avail + rep(v, each = n) + rnorm(n * m, 0, SE)
  data.frame(participant = factor(rep(1:n, m)), item = factor(rep(1:m, each = n)),
             avail = as.vector(avail), correct = rbinom(n * m, 1, plogis(as.vector(eta)))) }
rows <- list()
for (n in NS) for (m_items in MS) {
  glmm_hw <- paired_hw <- glmm_cov <- paired_cov <- est <- numeric(NSIM)
  for (s in 1:NSIM) {
    dd <- gen_trc(n, m_items)
    mod <- glmer(correct ~ avail + (1 + avail | participant) + (1 | item), data = dd, family = binomial,
                 control = glmerControl(optimizer = "bobyqa"))
    g <- pa_contrast(mod, data.frame(avail = 1), data.frame(avail = 0), avail_a = 1, avail_b = 0)
    wp <- aggregate(correct ~ participant + avail, data = dd, FUN = mean)
    dif <- wp$correct[wp$avail == 1] - wp$correct[wp$avail == 0]; tt <- t.test(dif)
    est[s] <- g["estimate"]; glmm_hw[s] <- (g["hi"] - g["lo"]) / 2; paired_hw[s] <- diff(tt$conf.int) / 2
    glmm_cov[s] <- g["lo"] <= 0.30 & g["hi"] >= 0.30; paired_cov[s] <- tt$conf.int[1] <= 0.30 & tt$conf.int[2] >= 0.30
    if (s %% 20 == 0) { cat(sprintf("n=%d m=%d sim=%d\n", n, m_items, s)); flush.console() }
  }
  rows[[length(rows) + 1]] <- data.frame(n = n, probe_items = m_items, nsim = NSIM,
    glmm_halfwidth_pp = 100 * mean(glmm_hw), paired_halfwidth_pp = 100 * mean(paired_hw),
    glmm_coverage = mean(glmm_cov), paired_coverage = mean(paired_cov), sd_estimate_pp = 100 * sd(est))
  write.csv(do.call(rbind, rows), file.path(outdir, "validation_trc_grid.csv"), row.names = FALSE)
}
cat("done\n")
