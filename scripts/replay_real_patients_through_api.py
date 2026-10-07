#!/usr/bin/env python3
"""
System-level replay: send every real, eligible patient through the product's HTTP
API (the real FastAPI routers, via TestClient) and check the answers.

This is an INTEGRATION test of the deployed surface (request parsing, vocabulary
mapping, model loading, response contract, latency) with real-world inputs.
It is NOT a performance validation: the shipped model was fitted on these same
patients, so metrics here are in-sample (the out-of-sample evidence is the
leave-one-cohort-out report). Use --report to write docs/validation/API_REPLAY_REPORT.md.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.v1.endpoints import cds, real_data  # noqa: E402
from app.services.cds.cox_prognostic_model import load_default_model  # noqa: E402
from app.services.real_data.cohort import apply_eligibility  # noqa: E402
from app.services.real_data.sources import load_all_cohorts  # noqa: E402
from app.services.validation.survival_metrics import concordance_index  # noqa: E402


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(cds.router, prefix="/api/v1/cds")
    app.include_router(real_data.router, prefix="/api/v1/real-data")
    return app


def request_body(row) -> dict:
    patient = {"gender": row.sex or None}
    if not np.isnan(row.age):
        patient["age"] = float(row.age)
    cancer = {"t_stage": row.t_stage, "n_stage": row.n_stage, "m_stage": row.m_stage,
              "histology": "Squamous cell carcinoma" if row.histology == "ESCC" else "Adenocarcinoma" if row.histology == "EAC" else ""}
    return {"patient_data": patient, "cancer_data": cancer}


def replay(limit=None, cache_dir=ROOT / "data/real_world/cache") -> dict:
    cohort, _ = load_all_cohorts(cache_dir=cache_dir)
    eligible, _ = apply_eligibility(cohort)
    if limit:
        eligible = eligible.groupby("cohort", group_keys=False).head(limit)
    client = TestClient(build_app())
    model = load_default_model()

    lps, latencies, failures, mismatches, contract_errors = [], [], 0, 0, 0
    for row in eligible.itertuples():
        body = request_body(row)
        t0 = time.perf_counter()
        resp = client.post("/api/v1/cds/prognostic-score-v2", json=body)
        latencies.append((time.perf_counter() - t0) * 1000)
        if resp.status_code != 200:
            failures += 1
            lps.append(np.nan)
            continue
        out = resp.json()
        lps.append(out["linear_predictor"])
        expected = model.predict_patient(body["patient_data"], body["cancer_data"])
        if abs(expected["linear_predictor"] - out["linear_predictor"]) > 1e-9:
            mismatches += 1
        ok = (
            set(out["survival"]) == {"1_year", "3_year"}  # 5y intentionally absent
            and 0 <= out["survival"]["3_year"] <= out["survival"]["1_year"] <= 1
            and out["risk_group"] in ("Low", "Intermediate", "High")
            and out["validation"]["status"].endswith("PASS")
        )
        contract_errors += 0 if ok else 1

    lps = np.array(lps, float)
    valid = ~np.isnan(lps)
    c = concordance_index(eligible["time_days"].to_numpy()[valid], eligible["event"].to_numpy(int)[valid],
                          lps[valid], eligible["cohort"].to_numpy()[valid])

    cat = client.get("/api/v1/real-data/catalog").json()
    val = client.get("/api/v1/real-data/validation?version=v2").json()
    legacy = client.post("/api/v1/cds/prognostic-score", json=request_body(next(eligible.itertuples())))
    return {
        "n_requests": int(len(eligible)),
        "http_failures": failures,
        "model_vs_http_mismatches": mismatches,
        "contract_errors": contract_errors,
        "latency_ms_p50": float(np.percentile(latencies, 50)),
        "latency_ms_p95": float(np.percentile(latencies, 95)),
        "in_sample_c_index_via_http": float(c),
        "catalog_total": cat["summary"]["total"],
        "validation_endpoint_all_passed": val["all_criteria_passed"],
        "legacy_endpoint_has_failure_notice": "FAILED" in legacy.json().get("validation_notice", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    r = replay()
    for k, v in r.items():
        print(f"{k}: {v}")
    ok = (r["http_failures"] == 0 and r["model_vs_http_mismatches"] == 0 and r["contract_errors"] == 0
          and r["legacy_endpoint_has_failure_notice"] and r["validation_endpoint_all_passed"])
    if args.report:
        md = f"""# گزارش replay سیستمی: بیماران واقعی از طریق API محصول

> تولید خودکار توسط `scripts/replay_real_patients_through_api.py`. این **تست یکپارچگی** است، نه اعتبارسنجی عملکرد:
> مدل منتشرشده روی همین بیماران برازش شده، پس C-index زیر درون‌نمونه‌ای (in-sample) است؛ شواهد برون‌نمونه‌ای در
> [گزارش v2](REAL_DATA_VALIDATION_REPORT_v2.md) آمده است.

| شاخص | مقدار |
|---|---|
| درخواست‌های واقعی ارسال‌شده به `POST /api/v1/cds/prognostic-score-v2` | {r['n_requests']} |
| خطای HTTP | {r['http_failures']} |
| ناسازگاری پاسخ HTTP با پیش‌بینی مستقیم مدل | {r['model_vs_http_mismatches']} |
| نقض قرارداد پاسخ (فقط افق ۱ و ۳ ساله، ترتیب احتمالات، گروه ریسک، برچسب اعتبارسنجی) | {r['contract_errors']} |
| تأخیر p50 / p95 (ms، درون‌فرایندی) | {r['latency_ms_p50']:.1f} / {r['latency_ms_p95']:.1f} |
| C-index درون‌نمونه‌ای از پاسخ‌های HTTP | {r['in_sample_c_index_via_http']:.3f} |
| `GET /real-data/catalog` — تعداد منابع | {r['catalog_total']} |
| `GET /real-data/validation?version=v2` — همه معیارها PASS | {r['validation_endpoint_all_passed']} |
| endpoint قدیمی `prognostic-score` هشدار «FAILED validation» می‌دهد | {r['legacy_endpoint_has_failure_notice']} |

نتیجه: {'✅ سطح API با ورودی‌های واقعی سازگار و پایدار است' if ok else '❌ ناسازگاری یافت شد'}

**محدودیت:** TestClient روی routerهای واقعی `cds` و `real_data` اجرا می‌شود، نه کل اپلیکیشن با میدلورها/پایگاه‌داده/Docker
(وابستگی‌های سنگین ML در این محیط نصب نیست). تأخیر درون‌فرایندی است و جایگزین تست بار روی استقرار واقعی نیست.
"""
        (ROOT / "docs/validation/API_REPLAY_REPORT.md").write_text(md, encoding="utf-8")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
