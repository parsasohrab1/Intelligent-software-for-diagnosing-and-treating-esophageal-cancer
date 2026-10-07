"""
Internal-external leave-one-cohort-out (LOCO) validation of the ridge-Cox
prognostic model. Implements docs/validation/VALIDATION_PROTOCOL_v2.md.
"""
from datetime import datetime, timezone
from typing import Dict, Optional

import numpy as np
import pandas as pd

from app.services.cds.cox_prognostic_model import FEATURES, CoxPrognosticModel
from app.services.real_data.cohort import apply_eligibility
from app.services.validation import survival_metrics as sm
from app.services.validation.real_data_validator import (
    CRITERIA,
    SEED,
    YEAR,
    _analyse,
    add_baselines,
    evaluate_criteria,
)

V2_CATEGORIES = ("Low", "Intermediate", "High")
N_BOOT_HR = 300


def _hazard_ratio_cis(df: pd.DataFrame, lam: float, base: Dict[str, float]) -> Dict:
    rng = np.random.default_rng(SEED)
    groups = [np.where(df["cohort"].values == c)[0] for c in df["cohort"].unique()]
    draws = []
    for _ in range(N_BOOT_HR):
        idx = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in groups])
        draws.append(CoxPrognosticModel().fit(df.iloc[idx], lam).hazard_ratios())
    out = {}
    for name in FEATURES:
        vals = [d[name] for d in draws]
        out[name] = {
            "hr": base[name],
            "ci95": [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))],
        }
    return out


def run_loco_validation(cohort_df: pd.DataFrame, provenance: Dict, protocol_commit: Optional[str] = None):
    """Returns (results_dict, final_model)."""
    eligible, flow = apply_eligibility(cohort_df)
    parts, folds = [], {}
    for held in eligible["cohort"].unique():
        train, test = eligible[eligible.cohort != held], eligible[eligible.cohort == held]
        model = CoxPrognosticModel.fit_with_cv(train)
        lp = model.linear_predictor(test)
        part = test.copy()
        part["risk_score"] = lp
        part["risk_category"] = model.risk_group(lp)
        for years in (1, 3, 5):
            part[f"pred_survival_{years}y"] = model.predict_survival(test, years * YEAR)
        parts.append(part)
        folds[held] = {
            "trained_on": sorted(train["cohort"].unique().tolist()),
            "n_train": int(len(train)),
            "lambda": model.lam,
            "lambda_cv_mean_c_index": model.training_summary["lambda_selection"]["cv_mean_c_index"],
            "hazard_ratios": model.hazard_ratios(),
        }

    scored = add_baselines(pd.concat(parts, ignore_index=True))
    per_cohort = {n: _analyse(sub, None, categories=V2_CATEGORIES) for n, sub in scored.groupby("cohort", sort=False)}
    pooled = _analyse(scored, "cohort", categories=V2_CATEGORIES)
    naive = sm.concordance_index(scored["time_days"], scored["event"].astype(int), scored["risk_score"])
    complete = scored[(scored.t_stage != "") & (scored.n_stage != "") & (scored.m_stage != "")]
    by_histology = {
        h: _analyse(sub, "cohort", boot=False, categories=V2_CATEGORIES)
        for h, sub in scored.groupby("histology") if h and len(sub) >= 30
    }

    final = CoxPrognosticModel.fit_with_cv(eligible)
    hrs = _hazard_ratio_cis(eligible, final.lam, final.hazard_ratios())

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocol": "docs/validation/VALIDATION_PROTOCOL_v2.md",
        "protocol_commit": protocol_commit,
        "model": "Ridge Cox PH (Breslow), leave-one-cohort-out",
        "criteria": {**CRITERIA, "A8_not_worse_than_stage_by": 0.01},
        "provenance": provenance,
        "participant_flow": flow,
        "loco_folds": folds,
        "per_cohort": per_cohort,
        "pooled_stratified": pooled,
        "sensitivity": {
            "naive_pooled_c_index": naive,
            "complete_tnm_subset": _analyse(complete, "cohort", categories=V2_CATEGORIES) if len(complete) else None,
            "by_histology": by_histology,
        },
        "final_model": {"lambda": final.lam, "hazard_ratios": hrs, "training_summary": final.training_summary},
        "verdict": evaluate_criteria(pooled, per_cohort, require_stage_baseline=True),
    }
    return results, final


def render_extra_markdown(r: Dict) -> str:
    L = ["\n## جزئیات LOCO\n", "| کوهورت نگه‌داشته‌شده | آموزش روی | n آموزش | λ انتخابی |\n|---|---|---|---|"]
    for h, f in r["loco_folds"].items():
        L.append(f"| {h} | {' + '.join(f['trained_on'])} | {f['n_train']} | {f['lambda']} |")
    L.append("\n## مدل نهایی (برازش روی هر سه کوهورت) — Hazard Ratio با bootstrap 95٪\n")
    L.append("| ویژگی | HR | CI 95٪ |\n|---|---|---|")
    for name, v in r["final_model"]["hazard_ratios"].items():
        unit = " (به‌ازای ۱ سال)" if name == "age" else ""
        L.append(f"| `{name}`{unit} | {v['hr']:.3f} | [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] |")
    return "\n".join(L) + "\n"
