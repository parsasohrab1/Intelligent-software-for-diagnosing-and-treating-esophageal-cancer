"""
Tests for the ridge-Cox prognostic model (network-free).

    pytest --noconftest --no-cov tests/test_cox_prognostic_model.py
"""
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import approx_fprime

from app.services.cds.cox_prognostic_model import (
    FEATURES,
    CoxPrognosticModel,
    _nll_and_grad,
    build_features,
)


def _simulate(n=1500, seed=3, beta_age=0.04, beta_t=0.5, beta_n=0.4):
    """Exponential survival with known log-hazard ratios and ~30% random censoring."""
    rng = np.random.default_rng(seed)
    age = rng.normal(62, 9, n)
    t_ord = rng.integers(1, 5, n)
    n_ord = rng.integers(0, 4, n)
    lp = beta_age * (age - 62) + beta_t * t_ord + beta_n * n_ord
    surv = rng.exponential(1.0 / (0.0008 * np.exp(lp)))
    cens = rng.exponential(1500, n)
    time = np.minimum(surv, cens)
    event = (surv <= cens).astype(int)
    return pd.DataFrame(
        {
            "age": age, "sex": rng.choice(["Male", "Female"], n), "histology": rng.choice(["ESCC", "EAC"], n),
            "t_stage": [f"T{x}" for x in t_ord], "n_stage": [f"N{x}" for x in n_ord], "m_stage": "M0",
            "time_days": time, "event": event,
        }
    )


class TestPartialLikelihood:
    def test_analytic_gradient_matches_finite_differences(self):
        df = _simulate(n=120)
        df.loc[df.index[:10], "time_days"] = df.loc[df.index[10:20], "time_days"].values  # create tied times
        model = CoxPrognosticModel()
        raw = build_features(df)
        model.age_mean, model.age_sd, model.t_median, model.n_median = raw.age.mean(), raw.age.std(ddof=0), 2.0, 1.0
        X = model._design(df)
        t, e = df.time_days.to_numpy(float), df.event.to_numpy(float)
        beta = np.random.default_rng(0).normal(0, 0.3, X.shape[1])
        _, grad = _nll_and_grad(beta, X, t, e, 1.0)
        num = approx_fprime(beta, lambda b: _nll_and_grad(b, X, t, e, 1.0)[0], 1e-6)
        assert np.allclose(grad, num, rtol=1e-4, atol=1e-4)

    def test_recovers_known_hazard_ratios(self):
        df = _simulate(n=4000, seed=11)
        m = CoxPrognosticModel().fit(df, lam=1e-6)
        beta = dict(zip(FEATURES, m.beta))
        assert beta["age"] / m.age_sd == pytest.approx(0.04, abs=0.01)
        assert beta["t_ord"] == pytest.approx(0.5, abs=0.07)
        assert beta["n_ord"] == pytest.approx(0.4, abs=0.07)
        assert abs(beta["male"]) < 0.12 and abs(beta["eac"]) < 0.12  # null covariates

    def test_ridge_shrinks_coefficients(self):
        df = _simulate(n=400, seed=5)
        weak = CoxPrognosticModel().fit(df, 0.1)
        strong = CoxPrognosticModel().fit(df, 100.0)
        assert np.linalg.norm(strong.beta) < np.linalg.norm(weak.beta)


class TestPrediction:
    def test_survival_is_monotone_decreasing_and_ordered_by_risk(self):
        df = _simulate(n=800, seed=2)
        m = CoxPrognosticModel().fit(df, 1.0)
        s1, s3, s5 = (m.predict_survival(df, y * 365.25) for y in (1, 3, 5))
        assert np.all((s1 >= s3) & (s3 >= s5)) and np.all((s1 <= 1) & (s5 >= 0))
        lp = m.linear_predictor(df)
        from scipy.stats import spearmanr
        assert spearmanr(lp, s3)[0] == pytest.approx(-1.0, abs=1e-9)  # strictly monotone: higher risk -> lower survival

    def test_json_round_trip_gives_identical_predictions(self, tmp_path):
        df = _simulate(n=300, seed=8)
        m = CoxPrognosticModel().fit(df, 10.0)
        path = tmp_path / "m.json"
        m.save(path)
        m2 = CoxPrognosticModel.load(path)
        assert np.allclose(m.linear_predictor(df), m2.linear_predictor(df))
        assert np.allclose(m.predict_survival(df, 730), m2.predict_survival(df, 730))
        assert (m.risk_group(m.linear_predictor(df)) == m2.risk_group(m2.linear_predictor(df))).all()

    def test_missing_staging_and_age_are_imputed_not_dropped(self):
        df = _simulate(n=300, seed=9)
        m = CoxPrognosticModel().fit(df, 10.0)
        probe = df.head(3).copy()
        probe.loc[probe.index[0], ["t_stage", "n_stage", "m_stage"]] = ""
        probe.loc[probe.index[1], "age"] = np.nan
        lp = m.linear_predictor(probe)
        assert lp.shape == (3,) and np.isfinite(lp).all()

    def test_lambda_selection_is_deterministic(self):
        df = _simulate(n=300, seed=4)
        a = CoxPrognosticModel.select_lambda(df, repeats=1)
        b = CoxPrognosticModel.select_lambda(df, repeats=1)
        assert a == b and a["best_lambda"] in (0.1, 1.0, 10.0, 100.0)
