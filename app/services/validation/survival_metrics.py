"""
Survival-analysis metrics used by the real-data validation (no external
survival package required: only numpy/scipy).

All functions take plain array-likes. ``event`` is 1 for death, 0 for censored.
Risk scores: higher = worse prognosis.
"""
from typing import Callable, Dict, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import chi2


def _arr(x, dtype=float) -> np.ndarray:
    return np.asarray(x, dtype=dtype)


def concordance_index(time, event, risk, strata: Optional[Sequence] = None) -> float:
    """Harrell's C-index.

    A pair (i, j) is comparable when i had an event and t_i < t_j. It is
    concordant when risk_i > risk_j; tied risks count 0.5. If ``strata`` is
    given, only pairs within the same stratum are compared (used to pool
    cohorts without comparing patients across different baseline hazards).
    """
    t, e, r = _arr(time), _arr(event, int), _arr(risk)
    comparable = (t[:, None] < t[None, :]) & (e[:, None] == 1)
    if strata is not None:
        s = np.asarray(strata)
        comparable &= s[:, None] == s[None, :]
    n = comparable.sum()
    if n == 0:
        return float("nan")
    concordant = ((r[:, None] > r[None, :]) & comparable).sum()
    tied = ((r[:, None] == r[None, :]) & comparable).sum()
    return float((concordant + 0.5 * tied) / n)


def time_dependent_auc(time, event, risk, horizon_days: float, strata: Optional[Sequence] = None) -> Dict:
    """Cumulative/dynamic AUC at ``horizon_days`` (unweighted).

    cases    = died at or before the horizon
    controls = still under observation after the horizon
    Patients censored before the horizon are excluded (their status at the
    horizon is unknown). Without IPCW weighting this can be biased under
    heavy censoring; it is reported alongside the C-index, not instead of it.
    """
    t, e, r = _arr(time), _arr(event, int), _arr(risk)
    cases = (t <= horizon_days) & (e == 1)
    controls = t > horizon_days
    pair = cases[:, None] & controls[None, :]
    if strata is not None:
        s = np.asarray(strata)
        pair &= s[:, None] == s[None, :]
    n = pair.sum()
    if n == 0:
        return {"auc": float("nan"), "n_cases": int(cases.sum()), "n_controls": int(controls.sum())}
    auc = (((r[:, None] > r[None, :]) & pair).sum() + 0.5 * ((r[:, None] == r[None, :]) & pair).sum()) / n
    return {"auc": float(auc), "n_cases": int(cases.sum()), "n_controls": int(controls.sum())}


def kaplan_meier(time, event) -> Tuple[np.ndarray, np.ndarray]:
    """Product-limit estimator. Returns (event_times, survival_after_each_time)."""
    t, e = _arr(time), _arr(event, int)
    times = np.unique(t[e == 1])
    surv, s = [], 1.0
    for tt in times:
        n_risk = (t >= tt).sum()
        d = ((t == tt) & (e == 1)).sum()
        s *= 1.0 - d / n_risk
        surv.append(s)
    return times, np.array(surv)


def km_survival_at(time, event, horizon_days: float) -> float:
    """KM survival probability at ``horizon_days`` (NaN if follow-up never reaches it)."""
    t = _arr(time)
    if t.size == 0 or t.max() < horizon_days:
        return float("nan")
    times, surv = kaplan_meier(time, event)
    idx = np.searchsorted(times, horizon_days, side="right") - 1
    return 1.0 if idx < 0 else float(surv[idx])


def median_follow_up_reverse_km(time, event) -> float:
    """Median follow-up via the reverse Kaplan-Meier method (censoring as the event)."""
    times, surv = kaplan_meier(time, 1 - _arr(event, int))
    below = np.where(surv <= 0.5)[0]
    return float(times[below[0]]) if below.size else float("nan")


def logrank_test(time, event, group) -> Dict:
    """Multi-group log-rank test (chi-square, k-1 degrees of freedom)."""
    t, e, g = _arr(time), _arr(event, int), np.asarray(group)
    labels = np.unique(g)
    k = len(labels)
    if k < 2:
        return {"chi2": float("nan"), "df": 0, "p_value": float("nan")}
    O, E, V = np.zeros(k), np.zeros(k), np.zeros((k, k))
    for tt in np.unique(t[e == 1]):
        at_risk = t >= tt
        n = at_risk.sum()
        died = (t == tt) & (e == 1)
        d = died.sum()
        nk = np.array([(at_risk & (g == lab)).sum() for lab in labels], dtype=float)
        dk = np.array([(died & (g == lab)).sum() for lab in labels], dtype=float)
        O += dk
        E += d * nk / n
        if n > 1:
            V += d * (n - d) / (n - 1) * (np.diag(nk) / n - np.outer(nk, nk) / n**2)
    z = (O - E)[: k - 1]
    stat = float(z @ np.linalg.pinv(V[: k - 1, : k - 1]) @ z)
    return {"chi2": stat, "df": k - 1, "p_value": float(chi2.sf(stat, k - 1))}


def bootstrap_ci(
    stat_fn: Callable[..., float],
    arrays: Sequence,
    strata: Optional[Sequence] = None,
    n_boot: int = 2000,
    seed: int = 20260507,
    alpha: float = 0.05,
) -> Dict:
    """Percentile bootstrap CI. Resampling is stratified by ``strata`` if given.

    ``stat_fn`` is called as ``stat_fn(*resampled_arrays, strata=resampled_strata)``
    when ``strata`` is provided, otherwise ``stat_fn(*resampled_arrays)``.
    """
    rng = np.random.default_rng(seed)
    arrays = [np.asarray(a) for a in arrays]
    n = len(arrays[0])
    s = None if strata is None else np.asarray(strata)
    groups = [np.arange(n)] if s is None else [np.where(s == lab)[0] for lab in np.unique(s)]
    values = []
    for _ in range(n_boot):
        idx = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in groups])
        args = [a[idx] for a in arrays]
        v = stat_fn(*args, strata=s[idx]) if s is not None else stat_fn(*args)
        if not np.isnan(v):
            values.append(v)
    if not values:
        return {"lower": float("nan"), "upper": float("nan"), "n_valid": 0}
    lo, hi = np.percentile(values, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"lower": float(lo), "upper": float(hi), "n_valid": len(values)}


def permutation_p_value(time, event, risk, strata=None, n_perm: int = 2000, seed: int = 20260507) -> float:
    """One-sided p: probability that a random risk ordering reaches the observed C-index."""
    rng = np.random.default_rng(seed)
    observed = concordance_index(time, event, risk, strata)
    r = _arr(risk)
    ge = 0
    for _ in range(n_perm):
        if strata is None:
            perm = rng.permutation(r)
        else:
            perm = r.copy()
            s = np.asarray(strata)
            for lab in np.unique(s):
                idx = np.where(s == lab)[0]
                perm[idx] = rng.permutation(r[idx])
        if concordance_index(time, event, perm, strata) >= observed:
            ge += 1
    return float((ge + 1) / (n_perm + 1))
