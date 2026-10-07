#!/usr/bin/env python3
"""
Run the pre-registered v2 validation (ridge Cox, leave-one-cohort-out).
See docs/validation/VALIDATION_PROTOCOL_v2.md.

    python scripts/run_real_data_validation_v2.py [--refresh]

Writes docs/validation/REAL_DATA_VALIDATION_REPORT_v2.md,
docs/validation/real_data_validation_results_v2.json and the candidate model
docs/validation/prognostic_cox_v2_candidate.json.
Exit code 0 = all criteria passed, 2 = at least one failed.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.real_data.sources import load_all_cohorts  # noqa: E402
from app.services.validation.loco_validator import render_extra_markdown, run_loco_validation  # noqa: E402
from app.services.validation.real_data_validator import render_markdown, save_results  # noqa: E402


def _protocol_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=%h", "--", "docs/validation/VALIDATION_PROTOCOL_v2.md"],
            cwd=ROOT, text=True,
        ).strip()
    except Exception:
        return "n/a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    cohort, provenance = load_all_cohorts(cache_dir=ROOT / "data/real_world/cache", refresh=args.refresh)
    results, final_model = run_loco_validation(cohort, provenance, protocol_commit=_protocol_commit())

    out = ROOT / "docs/validation"
    title = "گزارش اعتبارسنجی v2 — مدل Cox داده‌محور (Leave-One-Cohort-Out)"
    save_results(results, out / "REAL_DATA_VALIDATION_REPORT_v2.md", out / "real_data_validation_results_v2.json",
                 title=title, protocol_file="VALIDATION_PROTOCOL_v2.md")
    with open(out / "REAL_DATA_VALIDATION_REPORT_v2.md", "a", encoding="utf-8") as fh:
        fh.write(render_extra_markdown(results))
    final_model.save(out / "prognostic_cox_v2_candidate.json")

    verdict = results["verdict"]
    for k, c in verdict["checks"].items():
        print(f"{k}: {'PASS' if c['pass'] else 'FAIL'}  {c['desc']}  -> {c['value']}")
    print("ALL PASSED" if verdict["all_passed"] else "VALIDATION FAILED (see report)")
    return 0 if verdict["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
