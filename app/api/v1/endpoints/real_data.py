"""
Real-world data resources and validation evidence endpoints (read-only).
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.real_data.catalog import CATALOG, catalog_summary

router = APIRouter()

VALIDATION_DIR = Path(__file__).resolve().parents[4] / "docs" / "validation"
RESULT_FILES = {"v1": "real_data_validation_results.json", "v2": "real_data_validation_results_v2.json"}


@router.get("/catalog")
async def get_dataset_catalog(
    integration: Optional[str] = Query(None, description="validated | verified_only | not_integrated"),
    verification: Optional[str] = Query(None, description="live | literature"),
) -> Dict[str, Any]:
    """Real public datasets relevant to esophageal cancer, with what was and wasn't verified."""
    items = [
        e for e in CATALOG
        if (integration is None or e["integration"] == integration)
        and (verification is None or e["verification"] == verification)
    ]
    return {"summary": catalog_summary(), "datasets": items}


@router.get("/validation")
async def get_validation_evidence(version: str = Query("v2", description="v1 = rule-based scorer, v2 = Cox model")) -> Dict[str, Any]:
    """Headline results of the pre-registered real-data validation (full report in docs/validation/)."""
    if version not in RESULT_FILES:
        raise HTTPException(status_code=400, detail="version must be 'v1' or 'v2'")
    path = VALIDATION_DIR / RESULT_FILES[version]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Validation results not found; run scripts/run_real_data_validation*.py")
    r = json.loads(path.read_text(encoding="utf-8"))
    pooled = r["pooled_stratified"]
    return {
        "version": version,
        "model": r["model"],
        "protocol": r["protocol"],
        "generated_at": r["generated_at"],
        "all_criteria_passed": r["verdict"]["all_passed"],
        "criteria": {k: {"description": c["desc"], "passed": c["pass"]} for k, c in r["verdict"]["checks"].items()},
        "pooled_c_index": pooled["model"]["c_index"],
        "pooled_c_index_ci95": [pooled["model"]["ci95"]["lower"], pooled["model"]["ci95"]["upper"]],
        "baselines_c_index": {
            "ajcc_stage_only": pooled["baseline_stage_only"]["c_index"],
            "age_only": pooled["baseline_age_only"]["c_index"],
        },
        "per_cohort_c_index": {k: v["model"]["c_index"] for k, v in r["per_cohort"].items()},
        "participant_flow": r["participant_flow"],
        "data_provenance": {k: {"source": v["source"], "release": v.get("data_release"), "raw_sha256": v["raw_sha256"]}
                            for k, v in r["provenance"].items()},
        "report": f"docs/validation/REAL_DATA_VALIDATION_REPORT{'_v2' if version == 'v2' else ''}.md",
    }
