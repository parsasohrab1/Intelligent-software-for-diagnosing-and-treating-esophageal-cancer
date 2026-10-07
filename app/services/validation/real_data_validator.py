"""
Retrospective validation of ``PrognosticScorer`` on real public cohorts.

Implements docs/validation/VALIDATION_PROTOCOL.md exactly (including its
amendments). Only baseline, pre-treatment variables are given to the model.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Optional

import numpy as np
import pandas as pd

from app.services.cds.prognostic_scorer import PrognosticScorer
from app.services.real_data.cohort import DAYS_PER_MONTH, apply_eligibility
from app.services.real_data.normalize import stage_group_to_ordinal
from app.services.validation import survival_metrics as sm

YEAR = 365.25
N_BOOT = 2000
SEED = 20260507

# Pre-registered thresholds (docs/validation/VALIDATION_PROTOCOL.md, section 6)
CRITERIA = {
    "A1_c_index_pooled_min": 0.60,
    "A2_c_index_ci_lower_gt": 0.50,
    "A3_c_index_each_cohort_min": 0.55,
    "A4_auc_3y_pooled_min": 0.60,
    "A5_logrank_p_max": 0.05,
    "A6_calibration_1y_abs_error_max": 0.15,
    "A7_not_worse_than_age_baseline": True,
}


def score_patients(df: pd.DataFrame, scorer: Optional[PrognosticScorer] = None) -> pd.DataFrame:
    """Run the product's own scorer on each patient (baseline variables only)."""
    scorer = scorer or PrognosticScorer()
    out = df.copy()
    scores, cats, p1, p5 = [], [], [], []
    for _, row in df.iterrows():
        patient = {}
        if pd.notna(row["age"]):
            patient["age"] = float(row["age"])
        if row["sex"]:
            patient["gender"] = row["sex"]
        cancer = {"t_stage": row["t_stage"] or "", "n_stage": row["n_stage"] or "", "m_stage": row["m_stage"] or ""}
        res = scorer.calculate_prognostic_score(patient, cancer)
        scores.append(res["prognostic_score"])
        cats.append(res["category"])
        p1.append(res["survival_estimates"]["1_year_survival_rate"])
        p5.append(res["survival_estimates"]["5_year_survival_rate"])
    out["risk_score"] = scores
    out["risk_category"] = cats
    out["pred_survival_1y"] = p1
    out["pred_survival_5y"] = p5
    return add_baselines(out)


def add_baselines(out: pd.DataFrame) -> pd.DataFrame:
    """Reference predictors (higher = worse). Missing values imputed with the pooled median."""
    out = out.copy()
    stage_ord = out["stage_group"].map(stage_group_to_ordinal).astype(float)
    out["baseline_stage"] = stage_ord.fillna(stage_ord.median())
    out["baseline_age"] = out["age"].fillna(out["age"].median())
    return out


def _cindex_block(sub: pd.DataFrame, col: str, strata=None, boot: bool = True) -> Dict:
    t, e, r = sub["time_days"].values, sub["event"].values.astype(int), sub[col].values
    s = None if strata is None else sub[strata].values
    point = sm.concordance_index(t, e, r, s)
    block = {"c_index": point}
    if boot:
        block["ci95"] = sm.bootstrap_ci(
            lambda a, b, c, strata=None: sm.concordance_index(a, b, c, strata),
            [t, e, r], strata=s, n_boot=N_BOOT, seed=SEED,
        )
    return block


V1_CATEGORIES = ("Favorable", "Moderate", "Poor")


def _km_group_table(sub: pd.DataFrame, categories=V1_CATEGORIES) -> list:
    rows = []
    for cat in categories:
        g = sub[sub["risk_category"] == cat]
        if len(g) == 0:
            continue
        rows.append(
            {
                "category": cat,
                "n": int(len(g)),
                "events": int(g["event"].sum()),
                "km_survival_1y": sm.km_survival_at(g["time_days"], g["event"], YEAR),
                "km_survival_3y": sm.km_survival_at(g["time_days"], g["event"], 3 * YEAR),
            }
        )
    return rows


def _analyse(sub: pd.DataFrame, strata: Optional[str], boot: bool = True, categories=V1_CATEGORIES) -> Dict:
    t, e, s = sub["time_days"], sub["event"].astype(int), (None if strata is None else sub[strata].values)
    res = {
        "n": int(len(sub)),
        "events": int(e.sum()),
        "median_follow_up_months": sm.median_follow_up_reverse_km(t, e) / DAYS_PER_MONTH,
        "model": _cindex_block(sub, "risk_score", strata, boot),
        "baseline_stage_only": _cindex_block(sub, "baseline_stage", strata, boot=False),
        "baseline_age_only": _cindex_block(sub, "baseline_age", strata, boot=False),
        "auc_1y": sm.time_dependent_auc(t, e, sub["risk_score"], YEAR, s),
        "auc_3y": sm.time_dependent_auc(t, e, sub["risk_score"], 3 * YEAR, s),
        "risk_groups": _km_group_table(sub, categories),
        "n_distinct_risk_scores": int(sub["risk_score"].nunique()),
    }
    if boot:
        res["permutation_p_c_index"] = sm.permutation_p_value(t, e, sub["risk_score"], s, n_perm=1000, seed=SEED)
    groups = sub["risk_category"].values
    res["logrank"] = sm.logrank_test(t, e, groups)
    km1 = sm.km_survival_at(t, e, YEAR)
    pred1 = float(sub["pred_survival_1y"].mean())
    km5 = sm.km_survival_at(t, e, 5 * YEAR)
    res["calibration"] = {
        "km_survival_1y": km1,
        "mean_pred_survival_1y": pred1,
        "abs_error_1y": abs(km1 - pred1) if not np.isnan(km1) else float("nan"),
        "km_survival_5y": km5,  # informational only (Amendment 1)
        "mean_pred_survival_5y": float(sub["pred_survival_5y"].mean()),
    }
    if "pred_survival_3y" in sub:
        res["calibration"]["km_survival_3y"] = sm.km_survival_at(t, e, 3 * YEAR)
        res["calibration"]["mean_pred_survival_3y"] = float(sub["pred_survival_3y"].mean())
    return res


def evaluate_criteria(pooled: Dict, per_cohort: Dict, require_stage_baseline: bool = False) -> Dict:
    c = CRITERIA
    c_idx = pooled["model"]["c_index"]
    ci_lo = pooled["model"]["ci95"]["lower"]
    checks = {
        "A1": {"desc": f"pooled C-index >= {c['A1_c_index_pooled_min']}", "value": c_idx, "pass": c_idx >= c["A1_c_index_pooled_min"]},
        "A2": {"desc": f"CI95 lower bound > {c['A2_c_index_ci_lower_gt']}", "value": ci_lo, "pass": ci_lo > c["A2_c_index_ci_lower_gt"]},
        "A3": {
            "desc": f"C-index >= {c['A3_c_index_each_cohort_min']} in EVERY cohort",
            "value": {k: v["model"]["c_index"] for k, v in per_cohort.items()},
            "pass": all(v["model"]["c_index"] >= c["A3_c_index_each_cohort_min"] for v in per_cohort.values()),
        },
        "A4": {"desc": f"pooled AUC(3y) >= {c['A4_auc_3y_pooled_min']}", "value": pooled["auc_3y"]["auc"], "pass": pooled["auc_3y"]["auc"] >= c["A4_auc_3y_pooled_min"]},
        "A5": {"desc": f"log-rank p < {c['A5_logrank_p_max']}", "value": pooled["logrank"]["p_value"], "pass": pooled["logrank"]["p_value"] < c["A5_logrank_p_max"]},
        "A6": {
            "desc": f"|pred - KM| 1-year survival <= {c['A6_calibration_1y_abs_error_max']}",
            "value": pooled["calibration"]["abs_error_1y"],
            "pass": pooled["calibration"]["abs_error_1y"] <= c["A6_calibration_1y_abs_error_max"],
        },
        "A7": {
            "desc": "model C-index >= age-only baseline C-index",
            "value": {"model": c_idx, "age_only": pooled["baseline_age_only"]["c_index"]},
            "pass": c_idx >= pooled["baseline_age_only"]["c_index"],
        },
    }
    if require_stage_baseline:
        stage_c = pooled["baseline_stage_only"]["c_index"]
        checks["A8"] = {
            "desc": "model C-index >= AJCC-stage-only baseline - 0.01",
            "value": {"model": c_idx, "stage_only": stage_c},
            "pass": c_idx >= stage_c - 0.01,
        }
    for v in checks.values():
        v["pass"] = bool(v["pass"])
    return {"checks": checks, "all_passed": all(v["pass"] for v in checks.values())}


def run_validation(cohort_df: pd.DataFrame, provenance: Dict, protocol_commit: Optional[str] = None) -> Dict:
    eligible, flow = apply_eligibility(cohort_df)
    scored = score_patients(eligible)

    per_cohort = {name: _analyse(sub, None) for name, sub in scored.groupby("cohort", sort=False)}
    pooled = _analyse(scored, "cohort")
    # sensitivity: naive pooled C-index (compares patients across cohorts)
    naive = sm.concordance_index(scored["time_days"], scored["event"].astype(int), scored["risk_score"])

    complete = scored[(scored.t_stage != "") & (scored.n_stage != "") & (scored.m_stage != "")]
    subset_complete = _analyse(complete, "cohort") if len(complete) else None

    # histology sensitivity (pooled, stratified)
    by_histology = {
        h: _analyse(sub, "cohort", boot=False)
        for h, sub in scored.groupby("histology") if h and len(sub) >= 30
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocol": "docs/validation/VALIDATION_PROTOCOL.md",
        "protocol_commit": protocol_commit,
        "model": "PrognosticScorer (rule-based; not trained on these data)",
        "criteria": CRITERIA,
        "provenance": provenance,
        "participant_flow": flow,
        "per_cohort": per_cohort,
        "pooled_stratified": pooled,
        "sensitivity": {
            "naive_pooled_c_index": naive,
            "complete_tnm_subset": subset_complete,
            "by_histology": by_histology,
        },
        "verdict": evaluate_criteria(pooled, per_cohort),
    }


def _f(x, nd=3):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def render_markdown(
    r: Dict,
    title: str = "گزارش اعتبارسنجی با داده‌های واقعی — `PrognosticScorer`",
    protocol_file: str = "VALIDATION_PROTOCOL.md",
) -> str:
    p, v = r["pooled_stratified"], r["verdict"]
    L = []
    L.append(f"# {title}\n")
    L.append(f"> تولید خودکار: `{r['generated_at']}` — پروتکل: [`{protocol_file}`]({protocol_file})"
             f" (commit `{r.get('protocol_commit') or 'n/a'}`). اعداد زیر مستقیماً از اجرای اسکریپت اعتبارسنجی (`scripts/run_real_data_validation*.py`) آمده‌اند.\n")
    L.append(f"## نتیجهٔ کلی: {'✅ PASS — همهٔ معیارهای از پیش‌تعیین‌شده برقرار است' if v['all_passed'] else '❌ FAIL — حداقل یک معیار از پیش‌تعیین‌شده برقرار نیست'}\n")
    L.append("| معیار | شرح | مقدار | نتیجه |\n|---|---|---|---|")
    for k, c in v["checks"].items():
        val = c["value"]
        if isinstance(val, dict):
            val = ", ".join(f"{a}={_f(b)}" for a, b in val.items())
        else:
            val = _f(val, 4 if k == "A5" else 3)
        L.append(f"| {k} | {c['desc']} | {val} | {'✅' if c['pass'] else '❌'} |")
    L.append("\n## داده‌ها و منشأ (Provenance)\n")
    L.append("| کوهورت | منبع | نسخه/انتشار | SHA-256 (خام) |\n|---|---|---|---|")
    for name, pv in r["provenance"].items():
        L.append(f"| {name} | {pv['source']} | {pv.get('data_release') or 'n/a'} | `{pv['raw_sha256'][:16]}…` |")
    L.append("\n### جریان شرکت‌کنندگان (CONSORT-style)\n")
    L.append("| کوهورت | در منبع | حذف: زمان نامعتبر | حذف: وضعیت حیات ناموجود | واجد شرایط | مرگ |\n|---|---|---|---|---|---|")
    for name, f in r["participant_flow"].items():
        L.append(f"| {name} | {f['n_source']} | {f['excluded_invalid_follow_up_time']} | {f['excluded_missing_vital_status']} | {f['n_eligible']} | {f['n_events']} |")

    def block(title, a):
        out = [f"\n## {title}\n", f"n = **{a['n']}**، مرگ = **{a['events']}**، median follow-up (reverse KM) = **{_f(a['median_follow_up_months'],1)} ماه**\n"]
        m = a["model"]
        ci = m.get("ci95", {})
        out.append("| شاخص | مدل محصول | فقط مرحلهٔ AJCC | فقط سن |\n|---|---|---|---|")
        out.append(f"| C-index | **{_f(m['c_index'])}** [{_f(ci.get('lower'))}, {_f(ci.get('upper'))}] | {_f(a['baseline_stage_only']['c_index'])} | {_f(a['baseline_age_only']['c_index'])} |")
        out.append(f"\nAUC(1y) = {_f(a['auc_1y']['auc'])} (cases={a['auc_1y']['n_cases']}, controls={a['auc_1y']['n_controls']}) · "
                   f"AUC(3y) = {_f(a['auc_3y']['auc'])} (cases={a['auc_3y']['n_cases']}, controls={a['auc_3y']['n_controls']}) · "
                   f"log-rank p = {_f(a['logrank']['p_value'],4)} · تعداد مقادیر متمایز امتیاز = {a['n_distinct_risk_scores']}")
        if "permutation_p_c_index" in a:
            out.append(f" · permutation p (C-index) = {_f(a['permutation_p_c_index'],4)}")
        cal = a["calibration"]
        out.append(f"\n\nکالیبراسیون: بقای ۱ ساله KM = {_f(cal['km_survival_1y'])} در برابر میانگین پیش‌بینی مدل = {_f(cal['mean_pred_survival_1y'])} "
                   f"(|خطا| = {_f(cal['abs_error_1y'])})"
                   + (f" · ۳ ساله (اطلاعاتی): KM = {_f(cal['km_survival_3y'])}، مدل = {_f(cal['mean_pred_survival_3y'])}" if "km_survival_3y" in cal else "")
                   + f" · ۵ ساله (صرفاً اطلاعاتی): KM = {_f(cal['km_survival_5y'])}، مدل = {_f(cal['mean_pred_survival_5y'])}\n")
        if a["risk_groups"]:
            out.append("| گروه ریسک مدل | n | مرگ | بقای ۱ ساله KM | بقای ۳ ساله KM |\n|---|---|---|---|---|")
            for g in a["risk_groups"]:
                out.append(f"| {g['category']} | {g['n']} | {g['events']} | {_f(g['km_survival_1y'])} | {_f(g['km_survival_3y'])} |")
        return "\n".join(out)

    L.append(block("تحلیل اصلی: کوهورت تجمیعی (stratified)", p))
    for name, a in r["per_cohort"].items():
        L.append(block(f"کوهورت: {name}", a))
    s = r["sensitivity"]
    L.append(f"\n## تحلیل‌های حساسیت\n\n* C-index «naive» (مقایسهٔ آزاد بین کوهورت‌ها): **{_f(s['naive_pooled_c_index'])}**")
    if s["complete_tnm_subset"]:
        c = s["complete_tnm_subset"]
        L.append(f"* زیرمجموعهٔ TNM کامل (n={c['n']}): C-index = **{_f(c['model']['c_index'])}** [{_f(c['model']['ci95']['lower'])}, {_f(c['model']['ci95']['upper'])}]")
    for h, a in s["by_histology"].items():
        L.append(f"* هیستولوژی {h} (n={a['n']}): C-index = **{_f(a['model']['c_index'])}**، فقط-مرحله = {_f(a['baseline_stage_only']['c_index'])}، فقط-سن = {_f(a['baseline_age_only']['c_index'])}")
    L.append("\n## محدودیت‌ها\n\n"
             "* retrospective و روی داده‌های عمومی؛ جایگزین مطالعهٔ prospective یا تأیید رگولاتوری نیست.\n"
             "* مرحله‌بندی TCGA ترکیبی از ویرایش‌های مختلف AJCC است؛ GSE53624 و ICGC-ESCC فقط ESCC‌اند؛ برای GSE53624 فرض شده M0 (فقط مراحل I–III گزارش شده).\n"
             "* AUC وابسته به زمان بدون وزن‌دهی IPCW است. امتیاز مدل گسسته است (تعداد مقادیر متمایز آن کم است) و tie‌ها C-index را به ۰٫۵ نزدیک می‌کنند.\n"
             "* `RiskPredictor` (ریسک ابتلا) با داده‌های case-only قابل اعتبارسنجی نیست و در این گزارش ادعایی دربارهٔ آن نمی‌شود.\n")
    return "\n".join(L)


def save_results(results: Dict, md_path, json_path, **render_kwargs) -> None:
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else str(o))
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(results, **render_kwargs))
