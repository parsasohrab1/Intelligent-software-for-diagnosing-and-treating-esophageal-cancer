"""
Data-driven prognostic model: ridge-penalised Cox proportional hazards.

Replaces the hand-weighted ``PrognosticScorer`` heuristic with coefficients
estimated from real patients (see docs/validation/VALIDATION_PROTOCOL_v2.md).
Pure numpy/scipy; the fitted model serialises to plain JSON (no pickle).

Features are fixed up-front (no data-driven feature selection):
    age (standardised), male, t_ord (T1-4), n_ord (N0-3), m1, eac, tnm_missing
"""
import json
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from app.services.validation.survival_metrics import concordance_index

FEATURES = ["age", "male", "t_ord", "n_ord", "m1", "eac", "tnm_missing"]
LAMBDA_GRID = (0.1, 1.0, 10.0, 100.0)
YEAR = 365.25


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Raw (un-imputed) feature frame. Expects the unified cohort columns."""
    t = df["t_stage"].map({"T1": 1, "T2": 2, "T3": 3, "T4": 4})
    n = df["n_stage"].map({"N0": 0, "N1": 1, "N2": 2, "N3": 3})
    m = df["m_stage"].map({"M0": 0, "M1": 1})
    out = pd.DataFrame(
        {
            "age": pd.to_numeric(df["age"], errors="coerce"),
            "male": (df["sex"] == "Male").astype(float),
            "t_ord": t.astype(float),
            "n_ord": n.astype(float),
            "m1": m.astype(float),
            "eac": (df["histology"] == "EAC").astype(float),
            "tnm_missing": (t.isna() | n.isna() | m.isna()).astype(float),
        },
        index=df.index,
    )
    return out[FEATURES]


def _nll_and_grad(beta, X, t, e, lam):
    """Negative Breslow partial log-likelihood + ridge penalty, with gradient."""
    eta = X @ beta
    shift = eta.max()
    w = np.exp(eta - shift)
    ut, inv = np.unique(t, return_inverse=True)
    G, p = len(ut), X.shape[1]
    risk_w = np.cumsum(np.bincount(inv, weights=w, minlength=G)[::-1])[::-1]
    wx = np.zeros((G, p))
    np.add.at(wx, inv, w[:, None] * X)
    risk_wx = np.cumsum(wx[::-1], axis=0)[::-1]
    d = np.bincount(inv, weights=e, minlength=G)
    ev_eta = np.bincount(inv, weights=e * eta, minlength=G)
    ev_x = np.zeros((G, p))
    np.add.at(ev_x, inv, e[:, None] * X)

    loglik = np.sum(ev_eta - d * (shift + np.log(risk_w)))
    grad = -(ev_x - d[:, None] * risk_wx / risk_w[:, None]).sum(axis=0)
    return -loglik + 0.5 * lam * beta @ beta, grad + lam * beta


class CoxPrognosticModel:
    def __init__(self):
        self.beta: Optional[np.ndarray] = None
        self.lam: Optional[float] = None
        self.age_mean = self.age_sd = None
        self.t_median = self.n_median = None
        self.base_times: Optional[np.ndarray] = None
        self.base_cumhaz: Optional[np.ndarray] = None
        self.risk_cutoffs: Optional[List[float]] = None  # tertile cut-points of the linear predictor
        self.training_summary: Dict = {}

    # -- design matrix --------------------------------------------------
    def _design(self, df: pd.DataFrame) -> np.ndarray:
        f = build_features(df).copy()
        f["age"] = f["age"].fillna(self.age_mean)
        f["t_ord"] = f["t_ord"].fillna(self.t_median)
        f["n_ord"] = f["n_ord"].fillna(self.n_median)
        f["m1"] = f["m1"].fillna(0.0)
        f["age"] = (f["age"] - self.age_mean) / self.age_sd
        return f.to_numpy(dtype=float)

    # -- fitting --------------------------------------------------------
    def fit(self, df: pd.DataFrame, lam: float) -> "CoxPrognosticModel":
        raw = build_features(df)
        self.age_mean = float(raw["age"].mean())
        self.age_sd = float(raw["age"].std(ddof=0)) or 1.0
        self.t_median = float(raw["t_ord"].median())
        self.n_median = float(raw["n_ord"].median())
        X = self._design(df)
        t = df["time_days"].to_numpy(float)
        e = df["event"].to_numpy(float)
        res = minimize(
            _nll_and_grad, np.zeros(X.shape[1]), args=(X, t, e, lam),
            jac=True, method="L-BFGS-B", options={"maxiter": 500},
        )
        self.beta, self.lam = res.x, float(lam)

        # Breslow baseline cumulative hazard
        eta = X @ self.beta
        ut, inv = np.unique(t, return_inverse=True)
        w = np.exp(eta)
        risk_w = np.cumsum(np.bincount(inv, weights=w, minlength=len(ut))[::-1])[::-1]
        d = np.bincount(inv, weights=e, minlength=len(ut))
        self.base_times, self.base_cumhaz = ut, np.cumsum(d / risk_w)
        self.risk_cutoffs = [float(c) for c in np.quantile(eta, [1 / 3, 2 / 3])]
        self.training_summary = {"n": int(len(df)), "events": int(e.sum()), "converged": bool(res.success)}
        return self

    @staticmethod
    def select_lambda(df: pd.DataFrame, grid: Sequence[float] = LAMBDA_GRID, folds: int = 5, repeats: int = 3, seed: int = 20260507) -> Dict:
        """Choose ridge lambda by repeated K-fold CV (mean held-out C-index) on ``df`` only."""
        scores = {lam: [] for lam in grid}
        n = len(df)
        for rep in range(repeats):
            order = np.random.default_rng(seed + rep).permutation(n)
            fold_of = np.empty(n, int)
            fold_of[order] = np.arange(n) % folds
            for k in range(folds):
                tr, te = df.iloc[fold_of != k], df.iloc[fold_of == k]
                for lam in grid:
                    m = CoxPrognosticModel().fit(tr, lam)
                    c = concordance_index(te["time_days"], te["event"].astype(int), m.linear_predictor(te))
                    if not np.isnan(c):
                        scores[lam].append(c)
        mean = {lam: float(np.mean(v)) if v else float("nan") for lam, v in scores.items()}
        best = max(mean, key=lambda k: (mean[k] if not np.isnan(mean[k]) else -1))
        return {"best_lambda": best, "cv_mean_c_index": mean}

    @classmethod
    def fit_with_cv(cls, df: pd.DataFrame, **kw) -> "CoxPrognosticModel":
        sel = cls.select_lambda(df, **kw)
        model = cls().fit(df, sel["best_lambda"])
        model.training_summary["lambda_selection"] = sel
        return model

    # -- prediction -----------------------------------------------------
    def linear_predictor(self, df: pd.DataFrame) -> np.ndarray:
        return self._design(df) @ self.beta

    def cumulative_baseline_hazard(self, horizon_days: float) -> float:
        idx = np.searchsorted(self.base_times, horizon_days, side="right") - 1
        return 0.0 if idx < 0 else float(self.base_cumhaz[idx])

    def predict_survival(self, df: pd.DataFrame, horizon_days: float) -> np.ndarray:
        return np.exp(-self.cumulative_baseline_hazard(horizon_days) * np.exp(self.linear_predictor(df)))

    def risk_group(self, lp: np.ndarray) -> np.ndarray:
        lo, hi = self.risk_cutoffs
        return np.where(lp <= lo, "Low", np.where(lp <= hi, "Intermediate", "High"))

    def hazard_ratios(self) -> Dict[str, float]:
        scale = {"age": 1.0 / self.age_sd}  # per 1 year
        return {
            name: float(np.exp(b * scale.get(name, 1.0))) for name, b in zip(FEATURES, self.beta)
        }

    # -- (de)serialisation ---------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "model_type": "ridge_cox_breslow",
            "features": FEATURES,
            "beta": self.beta.tolist(),
            "lambda": self.lam,
            "age_mean": self.age_mean, "age_sd": self.age_sd,
            "t_median": self.t_median, "n_median": self.n_median,
            "base_times": self.base_times.tolist(),
            "base_cumhaz": self.base_cumhaz.tolist(),
            "risk_cutoffs": self.risk_cutoffs,
            "training_summary": self.training_summary,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CoxPrognosticModel":
        m = cls()
        m.beta = np.asarray(d["beta"], float)
        m.lam = d["lambda"]
        m.age_mean, m.age_sd = d["age_mean"], d["age_sd"]
        m.t_median, m.n_median = d["t_median"], d["n_median"]
        m.base_times = np.asarray(d["base_times"], float)
        m.base_cumhaz = np.asarray(d["base_cumhaz"], float)
        m.risk_cutoffs = d["risk_cutoffs"]
        m.training_summary = d.get("training_summary", {})
        return m

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item())

    @classmethod
    def load(cls, path) -> "CoxPrognosticModel":
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
