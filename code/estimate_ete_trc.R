## =====================================================================
##  estimate_ete_trc.R
##  Estimating the Epistemic Transfer Effect (ETE) and the Tool-Removal
##  Cost (TRC) from a two-wave dataset in long format.
##
##  Input columns: participant, arm, phase (baseline/probe/delayed), item,
##                 position, distance (delayed only), tool_available (0/1),
##                 correct (0/1), baseline_mean
##  Usage: Rscript estimate_ete_trc.R [path/to/data.csv] [SESOI in pp]
##  Requires: lme4 (nothing else).
## =====================================================================
suppressMessages(library(lme4))
args   <- commandArgs(trailingOnly = TRUE)
infile <- if (length(args) >= 1) args[1] else file.path("..", "data", "simulated_two_wave.csv")
SESOI  <- if (length(args) >= 2) as.numeric(args[2]) / 100 else 0.05
outdir <- file.path(dirname(infile), "..", "results"); dir.create(outdir, showWarnings = FALSE)

d <- read.csv(infile)
d$arm <- factor(d$arm, levels = c("active_practice", "answer_first_ai", "evidence_first_ai", "no_practice"))
pmean <- tapply(d$baseline_mean, d$participant, mean)
d$baseline_c <- d$baseline_mean - mean(pmean)       # centred baseline accuracy (precision covariate)

## ---- Population-averaged probabilities -------------------------------
## The estimands are defined as differences in population-average accuracy.
## A logistic mixed model gives conditional (participant- and item-specific)
## probabilities; we therefore integrate the fitted linear predictor over the
## estimated random-effect distribution (Gauss-Hermite quadrature) and
## propagate fixed-effect uncertainty by simulation. This returns contrasts
## in percentage points with confidence intervals.
gauss_hermite <- function(m = 40) {              # nodes/weights for N(0,1) (Golub-Welsch)
  i <- seq_len(m - 1); J <- matrix(0, m, m)
  J[cbind(i, i + 1)] <- sqrt(i); J[cbind(i + 1, i)] <- sqrt(i)
  e <- eigen(J, symmetric = TRUE); list(x = e$values, w = e$vectors[1, ]^2)
}
GH <- gauss_hermite(40)
pa_prob <- function(eta, s) vapply(eta, function(e) sum(GH$w * plogis(e + s * GH$x)), numeric(1))

re_sd <- function(model, avail = 0) {             # total random-effect SD for a row (handles a random slope on 'avail')
  vc <- VarCorr(model); v <- 0
  for (g in names(vc)) {
    M <- as.matrix(vc[[g]]); nm <- rownames(M)
    if (length(nm) == 1) v <- v + M[1, 1] else {
      a <- c(1, avail)[seq_along(nm)]; v <- v + as.numeric(t(a) %*% M %*% a)
    }
  }
  sqrt(v)
}

pa_contrast <- function(model, nd_a, nd_b, avail_a = 0, avail_b = 0, R = 4000, seed = 1) {
  ## Population-averaged accuracy under nd_a minus under nd_b, rows averaged with equal weight.
  set.seed(seed)
  b <- fixef(model); V <- as.matrix(vcov(model))
  draws <- t(b + t(chol(V)) %*% matrix(rnorm(R * length(b)), length(b), R))   # R x p
  f <- delete.response(terms(model, fixed.only = TRUE))
  Xa <- model.matrix(f, nd_a); Xb <- model.matrix(f, nd_b)
  sa <- re_sd(model, avail_a); sb <- re_sd(model, avail_b)
  pa <- apply(draws, 1, function(bb) mean(pa_prob(Xa %*% bb, sa)))
  pb <- apply(draws, 1, function(bb) mean(pa_prob(Xb %*% bb, sb)))
  diff <- pa - pb
  c(estimate = mean(diff), ci95_lo = unname(quantile(diff, .025)), ci95_hi = unname(quantile(diff, .975)),
    ci90_lo = unname(quantile(diff, .05)),  ci90_hi = unname(quantile(diff, .95)),
    p_a = mean(pa), p_b = mean(pb))
}
decide <- function(x, sesoi = SESOI) {
  superior   <- x["ci95_lo"] > 0 | x["ci95_hi"] < 0
  equivalent <- x["ci90_lo"] > -sesoi & x["ci90_hi"] < sesoi      # TOST at alpha = .05
  c(x * 100, superior = unname(superior), equivalent = unname(equivalent))
}

## ---- ETE: delayed unassisted test -------------------------------------
dl <- d[d$phase == "delayed", ]
dl$distance <- factor(dl$distance, levels = c("near", "intermediate", "far"))
cat("Fitting ETE model (main effects)...\n")
m_ete  <- glmer(correct ~ arm + distance + baseline_c + (1 | participant) + (1 | item),
                data = dl, family = binomial, control = glmerControl(optimizer = "bobyqa"))
cat("Fitting ETE model (arm x distance)...\n")
m_etex <- glmer(correct ~ arm * distance + baseline_c + (1 | participant) + (1 | item),
                data = dl, family = binomial, control = glmerControl(optimizer = "bobyqa"))
print(VarCorr(m_ete))

nd <- function(arm, dist = levels(dl$distance)) data.frame(arm = factor(arm, levels = levels(dl$arm)),
                                                          distance = factor(dist, levels = levels(dl$distance)),
                                                          baseline_c = 0)
res <- list()
for (a in c("answer_first_ai", "evidence_first_ai", "no_practice")) {
  res[[paste0("ETE_", a, "_vs_active_practice")]] <- decide(pa_contrast(m_ete, nd(a), nd("active_practice")))
  for (a2 in c("answer_first_ai", "evidence_first_ai"))
    if (a == "no_practice")
      res[[paste0("ETE_", a2, "_vs_no_practice")]] <- decide(pa_contrast(m_ete, nd(a2), nd("no_practice")))
}
for (dist in levels(dl$distance)) for (a in c("answer_first_ai", "evidence_first_ai"))
  res[[paste0("ETE_", a, "_vs_active_practice_", dist)]] <- decide(pa_contrast(m_etex, nd(a, dist), nd("active_practice", dist)))

## participant-level check (ANCOVA on mean delayed accuracy)
pl <- aggregate(correct ~ participant + arm + baseline_c, data = dl, FUN = mean)
fit_pl <- lm(correct ~ arm + baseline_c, data = pl)
ci <- confint(fit_pl)
for (a in c("answer_first_ai", "evidence_first_ai", "no_practice")) {
  k <- paste0("arm", a)
  res[[paste0("ETE_check_participant_level_", a, "_vs_active_practice")]] <-
    c(estimate = unname(coef(fit_pl)[k]) * 100, ci95_lo = ci[k, 1] * 100, ci95_hi = ci[k, 2] * 100)
}


## ---- Two-way cluster-robust linear probability model (transparent alternative) ----
## Trial-level accuracy regressed on arm (and baseline), with a sandwich variance that
## clusters on participants AND items (Cameron, Gelbach & Miller, 2011). Targets the same
## population-average difference as the marginal contrast; the item cluster carries
## item-specific variation in the arm effect. Critical value: t with min(clusters) - 1 df.
twoway_cr_lpm <- function(formula, data, cl1, cl2) {
  X <- model.matrix(formula, data); y <- model.response(model.frame(formula, data))
  XtX_inv <- solve(crossprod(X)); b <- XtX_inv %*% crossprod(X, y); e <- as.vector(y - X %*% b)
  Xe <- X * e
  meat <- function(cl) { S <- rowsum(Xe, cl); G <- nrow(S); crossprod(S) * G / (G - 1) }
  V <- XtX_inv %*% (meat(cl1) + meat(cl2) - crossprod(Xe)) %*% XtX_inv
  df <- min(length(unique(cl1)), length(unique(cl2))) - 1
  list(coef = as.vector(b), se = sqrt(diag(V)), df = df, names = colnames(X))
}
for (a in c("answer_first_ai", "evidence_first_ai", "no_practice")) {
  sub <- dl[dl$arm %in% c("active_practice", a), ]; sub$treat <- as.numeric(sub$arm == a)
  f <- twoway_cr_lpm(correct ~ treat + baseline_c, sub, sub$participant, sub$item)
  k <- which(f$names == "treat"); tq <- qt(0.975, f$df); tq90 <- qt(0.95, f$df)
  res[[paste0("ETE_check_twoway_CR_", a, "_vs_active_practice")]] <-
    c(estimate = unname(f$coef[k]) * 100, ci95_lo = unname(f$coef[k] - tq * f$se[k]) * 100, ci95_hi = unname(f$coef[k] + tq * f$se[k]) * 100,
      ci90_lo = unname(f$coef[k] - tq90 * f$se[k]) * 100, ci90_hi = unname(f$coef[k] + tq90 * f$se[k]) * 100)
}

## ---- TRC: immediate removal probe (AI arms only) ----------------------
pr <- d[d$phase == "probe" & d$arm %in% c("answer_first_ai", "evidence_first_ai"), ]
pr$arm <- droplevels(pr$arm); pr$avail <- pr$tool_available; pr$pos_c <- pr$position - mean(pr$position)
cat("Fitting TRC model...\n")
m_trc <- glmer(correct ~ avail * arm + pos_c + (1 + avail | participant) + (1 | item),
               data = pr, family = binomial, control = glmerControl(optimizer = "bobyqa"))
print(VarCorr(m_trc))
ndp <- function(arm, avail) data.frame(arm = factor(arm, levels = levels(pr$arm)), avail = avail, pos_c = 0)
for (a in levels(pr$arm))
  res[[paste0("TRC_", a)]] <- decide(pa_contrast(m_trc, ndp(a, 1), ndp(a, 0), avail_a = 1, avail_b = 0))

## within-person check: mean(with tool) - mean(without) per participant
wp <- aggregate(correct ~ participant + arm + avail, data = pr, FUN = mean)
wpw <- reshape(wp, idvar = c("participant", "arm"), timevar = "avail", direction = "wide")
wpw$diff <- wpw$correct.1 - wpw$correct.0
for (a in levels(pr$arm)) {
  tt <- t.test(wpw$diff[wpw$arm == a])
  res[[paste0("TRC_check_within_person_", a)]] <- c(estimate = unname(tt$estimate) * 100, ci95_lo = tt$conf.int[1] * 100, ci95_hi = tt$conf.int[2] * 100)
}

## ---- write ---------------------------------------------------------------
cols <- c("estimate", "ci95_lo", "ci95_hi", "ci90_lo", "ci90_hi", "p_a", "p_b", "superior", "equivalent")
tab <- do.call(rbind, lapply(names(res), function(n) {
  x <- res[[n]]; row <- setNames(as.list(rep(NA_real_, length(cols))), cols)
  for (cn in intersect(cols, names(x))) row[[cn]] <- round(unname(x[cn]), 2)
  data.frame(contrast = n, as.data.frame(row))
}))
print(tab, row.names = FALSE)
write.csv(tab, file.path(outdir, "worked_example_results.csv"), row.names = FALSE)
saveRDS(list(m_ete = m_ete, m_etex = m_etex, m_trc = m_trc), file.path(outdir, "worked_example_models.rds"))
cat("Written:", file.path(outdir, "worked_example_results.csv"), "\n")
