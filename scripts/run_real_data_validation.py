#!/usr/bin/env python3
"""
Run the pre-registered real-data validation (docs/validation/VALIDATION_PROTOCOL.md).

    python scripts/run_real_data_validation.py [--refresh]

Downloads (or reuses cached) public cohorts from GDC / GEO / cBioPortal, scores
every patient with the product's PrognosticScorer, and writes
docs/validation/REAL_DATA_VALIDATION_REPORT.md and
docs/validation/real_data_validation_results.json.
Exit code 0 = all pre-registered criteria passed, 2 = at least one failed.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.real_data.sources import load_all_cohorts  # noqa: E402
from app.services.validation.real_data_validator import run_validation, save_results  # noqa: E402


def _protocol_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=%h", "--", "docs/validation/VALIDATION_PROTOCOL.md"],
            cwd=ROOT, text=True,
        ).strip()
    except Exception:
        return "n/a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download raw snapshots")
    args = ap.parse_args()

    cohort, provenance = load_all_cohorts(cache_dir=ROOT / "data/real_world/cache", refresh=args.refresh)
    results = run_validation(cohort, provenance, protocol_commit=_protocol_commit())
    out = ROOT / "docs/validation"
    save_results(results, out / "REAL_DATA_VALIDATION_REPORT.md", out / "real_data_validation_results.json")

    verdict = results["verdict"]
    for k, c in verdict["checks"].items():
        print(f"{k}: {'PASS' if c['pass'] else 'FAIL'}  {c['desc']}  -> {c['value']}")
    print("ALL PASSED" if verdict["all_passed"] else "VALIDATION FAILED (see report)")
    return 0 if verdict["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
