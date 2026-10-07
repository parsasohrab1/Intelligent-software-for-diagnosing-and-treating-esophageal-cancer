#!/usr/bin/env python3
"""
Ship the validated Cox model with the product - but ONLY if the pre-registered
validation passed. Reads docs/validation/real_data_validation_results_v2.json
and docs/validation/prognostic_cox_v2_candidate.json, refuses to export when
``verdict.all_passed`` is false, and writes app/services/cds/prognostic_cox_v2.json
with a ``validation`` block embedded so every prediction carries its evidence.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.cds.cox_prognostic_model import DEFAULT_MODEL_PATH, CoxPrognosticModel  # noqa: E402


def main() -> int:
    vdir = ROOT / "docs/validation"
    results = json.loads((vdir / "real_data_validation_results_v2.json").read_text(encoding="utf-8"))
    if not results["verdict"]["all_passed"]:
        print("REFUSING to export: pre-registered validation did not pass.", file=sys.stderr)
        return 2

    model = CoxPrognosticModel.load(vdir / "prognostic_cox_v2_candidate.json")
    pooled = results["pooled_stratified"]
    model.validation = {
        "status": "retrospective_public_cohorts_pre_registered_PASS",
        "intended_use": "research / clinical decision support under clinician oversight; NOT a certified medical device",
        "protocol": "docs/validation/VALIDATION_PROTOCOL_v2.md",
        "report": "docs/validation/REAL_DATA_VALIDATION_REPORT_v2.md",
        "design": "internal-external leave-one-cohort-out",
        "cohorts": {k: {"n": v["n"], "events": v["events"]} for k, v in results["per_cohort"].items()},
        "data_provenance": {
            k: {"source": v["source"], "release": v.get("data_release"), "raw_sha256": v["raw_sha256"]}
            for k, v in results["provenance"].items()
        },
        "pooled_c_index": round(pooled["model"]["c_index"], 3),
        "pooled_c_index_ci95": [round(pooled["model"]["ci95"]["lower"], 3), round(pooled["model"]["ci95"]["upper"], 3)],
        "per_cohort_c_index": {k: round(v["model"]["c_index"], 3) for k, v in results["per_cohort"].items()},
        "auc_3y": round(pooled["auc_3y"]["auc"], 3),
        "validated_horizons": ["1_year", "3_year"],
        "not_validated": [
            "5_year survival (calibration inconsistent across cohorts)",
            "EAC-specific performance (n=89; C-index 0.565)",
            "any treatment-effect claim",
        ],
        "posthoc_vs_stage_only": results["exploratory_post_hoc"]["vs_stage_only"],
        "generated_at": results["generated_at"],
    }
    model.save(DEFAULT_MODEL_PATH)
    print(f"exported -> {DEFAULT_MODEL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
