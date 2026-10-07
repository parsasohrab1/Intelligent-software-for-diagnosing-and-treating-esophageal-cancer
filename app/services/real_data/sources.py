"""
Connectors for real, openly accessible esophageal-cancer cohorts.

Each ``fetch_*`` function:
  * downloads (or re-uses a cached raw snapshot of) the public source,
  * returns ``(cohort_df, provenance)`` where ``provenance`` records the
    source URL, retrieval time, source data-release/version and a SHA-256 of
    the raw snapshot, so a validation report can be traced to exact data.

Network access is required only on first use (or ``refresh=True``).
"""
import gzip
import hashlib
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import requests

from app.services.real_data.cohort import DAYS_PER_MONTH, finalize_cohort
from app.services.real_data.normalize import (
    histology_from_text,
    normalize_m,
    normalize_n,
    normalize_sex,
    normalize_t,
    parse_tnm_string,
    stage_group,
)

GDC_BASE = "https://api.gdc.cancer.gov"
CBIO_BASE = "https://www.cbioportal.org/api"
GEO_MATRIX_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE53nnn/GSE53624/matrix/"
    "GSE53624_series_matrix.txt.gz"
)
DEFAULT_CACHE_DIR = Path("data/real_world/cache")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get(url: str, retries: int = 4, timeout: int = 90, **kwargs) -> requests.Response:
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as exc:  # network flakiness: back off and retry
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} attempts: {last}")


def _load_or_fetch(cache_file: Path, fetch_bytes, refresh: bool) -> bytes:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    if cache_file.exists() and not refresh:
        return cache_file.read_bytes()
    data = fetch_bytes()
    cache_file.write_bytes(data)
    return data


def _provenance(source: str, url: str, raw: bytes, **extra) -> Dict:
    return {
        "source": source,
        "url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw_sha256": _sha256(raw),
        "raw_bytes": len(raw),
        **extra,
    }


# --------------------------------------------------------------------------
# TCGA-ESCA via NCI GDC
# --------------------------------------------------------------------------
def parse_gdc_cases(hits: list) -> pd.DataFrame:
    """Map GDC ``/cases`` hits (expand=demographic,diagnoses,follow_ups) to the unified schema."""
    rows = []
    for h in hits:
        demo = h.get("demographic") or {}
        primary = [d for d in h.get("diagnoses", []) if d.get("diagnosis_is_primary_disease")]
        dx = primary[0] if primary else {}

        vital = str(demo.get("vital_status") or "").lower()
        event = 1 if vital == "dead" else (0 if vital == "alive" else None)

        # days_to_* in GDC are relative to the index (diagnosis) date.
        if event == 1:
            time_days = demo.get("days_to_death")
        else:
            candidates = [dx.get("days_to_last_follow_up")] + [
                f.get("days_to_follow_up") for f in h.get("follow_ups", [])
            ]
            candidates = [c for c in candidates if c is not None]
            time_days = max(candidates) if candidates else None

        age = demo.get("age_at_index")
        if age is None and dx.get("age_at_diagnosis") is not None:
            age = dx["age_at_diagnosis"] / 365.25

        rows.append(
            {
                "cohort": "TCGA-ESCA",
                "patient_id": h.get("submitter_id"),
                "age": age,
                "sex": normalize_sex(demo.get("sex_at_birth") or demo.get("gender")),
                "histology": histology_from_text(dx.get("primary_diagnosis")),
                "t_stage": normalize_t(dx.get("ajcc_pathologic_t")),
                "n_stage": normalize_n(dx.get("ajcc_pathologic_n")),
                "m_stage": normalize_m(dx.get("ajcc_pathologic_m")),
                "stage_group": stage_group(dx.get("ajcc_pathologic_stage")),
                "time_days": time_days,
                "event": event,
            }
        )
    return finalize_cohort(rows)


def fetch_tcga_esca(cache_dir: Path = DEFAULT_CACHE_DIR, refresh: bool = False) -> Tuple[pd.DataFrame, Dict]:
    url = f"{GDC_BASE}/cases"
    params = {
        "filters": json.dumps(
            {"op": "in", "content": {"field": "project.project_id", "value": ["TCGA-ESCA"]}}
        ),
        "expand": "demographic,diagnoses,exposures,follow_ups",
        "size": "500",
        "format": "JSON",
    }
    raw = _load_or_fetch(
        Path(cache_dir) / "tcga_esca_gdc_cases.json",
        lambda: _get(url, params=params).content,
        refresh,
    )
    release = None
    try:
        release = _get(f"{GDC_BASE}/status", retries=2, timeout=30).json().get("data_release")
    except Exception:
        pass
    hits = json.loads(raw)["data"]["hits"]
    return parse_gdc_cases(hits), _provenance(
        "NCI GDC (TCGA-ESCA)", url, raw, data_release=release, access="open"
    )


# --------------------------------------------------------------------------
# GSE53624 (ESCC, China) via NCBI GEO series matrix header
# --------------------------------------------------------------------------
def parse_geo_series_matrix_header(text: str) -> pd.DataFrame:
    """Parse the ``!Sample_characteristics_ch1`` block of GSE53624.

    The series has a tumour and a matched-normal sample per patient; clinical
    values are duplicated across both, so we keep one row per patient.
    """
    chars: Dict[str, list] = {}
    for line in text.splitlines():
        if not line.startswith("!Sample_characteristics_ch1"):
            continue
        vals = [v.strip('"') for v in line.split("\t")[1:]]
        key = vals[0].split(":", 1)[0].strip().lower()
        chars[key] = [v.split(":", 1)[1].strip() if ":" in v else "" for v in vals]

    n = len(chars["patient id"])
    seen, rows = set(), []
    for i in range(n):
        pid = chars["patient id"][i]
        if pid in seen:
            continue
        seen.add(pid)
        death = chars["death at fu"][i].lower()
        months = pd.to_numeric(chars["survival time(months)"][i], errors="coerce")
        rows.append(
            {
                "cohort": "GSE53624",
                "patient_id": pid,
                "age": pd.to_numeric(chars["age"][i], errors="coerce"),
                "sex": normalize_sex(chars["sex"][i]),
                "histology": "ESCC",
                "t_stage": normalize_t(chars["t stage"][i]),
                "n_stage": normalize_n(chars["n stage"][i]),
                "m_stage": "M0",  # resected cohort; M1 not part of TNM stage I-III reported
                "stage_group": stage_group(chars["tnm stage"][i]),
                "time_days": months * DAYS_PER_MONTH if pd.notna(months) else None,
                "event": 1 if death == "yes" else (0 if death == "no" else None),
            }
        )
    return finalize_cohort(rows)


def fetch_gse53624(cache_dir: Path = DEFAULT_CACHE_DIR, refresh: bool = False) -> Tuple[pd.DataFrame, Dict]:
    cache_file = Path(cache_dir) / "gse53624_series_matrix_header.txt"

    def _download_header() -> bytes:
        # Stream the (69 MB) gz and keep only the header up to the data table.
        with requests.get(GEO_MATRIX_URL, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            lines = []
            for line in io.TextIOWrapper(gzip.GzipFile(fileobj=resp.raw), encoding="utf-8", errors="replace"):
                if line.startswith("!series_matrix_table_begin"):
                    break
                lines.append(line)
        return "".join(lines).encode("utf-8")

    raw = _load_or_fetch(cache_file, _download_header, refresh)
    return parse_geo_series_matrix_header(raw.decode("utf-8")), _provenance(
        "NCBI GEO GSE53624", GEO_MATRIX_URL, raw, access="open",
        note="Clinical characteristics block only (expression matrix not downloaded).",
    )


# --------------------------------------------------------------------------
# ICGC-ESCC (Nature 2014) via cBioPortal
# --------------------------------------------------------------------------
def parse_cbioportal_icgc_escc(patient_rows: list, sample_rows: list) -> pd.DataFrame:
    patients: Dict[str, Dict] = {}
    for r in patient_rows:
        patients.setdefault(r["patientId"], {})[r["clinicalAttributeId"]] = r["value"]
    samples: Dict[str, Dict] = {}
    for r in sample_rows:
        samples.setdefault(r["patientId"], {})[r["clinicalAttributeId"]] = r["value"]

    rows = []
    for pid, p in patients.items():
        s = samples.get(pid, {})
        t, n, m = parse_tnm_string(s.get("TNM"))
        status = str(p.get("OS_STATUS", ""))
        months = pd.to_numeric(p.get("OS_MONTHS"), errors="coerce")
        rows.append(
            {
                "cohort": "ICGC-ESCC",
                "patient_id": pid,
                "age": pd.to_numeric(p.get("AGE"), errors="coerce"),
                "sex": normalize_sex(p.get("SEX")),
                "histology": "ESCC",
                "t_stage": t,
                "n_stage": n,
                "m_stage": m,
                "stage_group": stage_group(s.get("TUMOR_STAGE")),
                "time_days": months * DAYS_PER_MONTH if pd.notna(months) else None,
                "event": 1 if status.startswith("1") else (0 if status.startswith("0") else None),
            }
        )
    return finalize_cohort(rows)


def fetch_icgc_escc(cache_dir: Path = DEFAULT_CACHE_DIR, refresh: bool = False) -> Tuple[pd.DataFrame, Dict]:
    study = "escc_icgc"
    cache_file = Path(cache_dir) / "icgc_escc_cbioportal.json"

    def _download() -> bytes:
        out = {}
        for kind in ("PATIENT", "SAMPLE"):
            url = f"{CBIO_BASE}/studies/{study}/clinical-data"
            out[kind] = _get(url, params={"clinicalDataType": kind, "projection": "DETAILED"}).json()
        return json.dumps(out).encode("utf-8")

    raw = _load_or_fetch(cache_file, _download, refresh)
    data = json.loads(raw)
    return parse_cbioportal_icgc_escc(data["PATIENT"], data["SAMPLE"]), _provenance(
        "cBioPortal escc_icgc (ICGC, Nature 2014)", f"{CBIO_BASE}/studies/{study}", raw, access="open"
    )


SOURCES = {
    "TCGA-ESCA": fetch_tcga_esca,
    "GSE53624": fetch_gse53624,
    "ICGC-ESCC": fetch_icgc_escc,
}


def load_all_cohorts(cache_dir: Path = DEFAULT_CACHE_DIR, refresh: bool = False) -> Tuple[pd.DataFrame, Dict]:
    frames, provenance = [], {}
    for name, fetch in SOURCES.items():
        df, prov = fetch(cache_dir=cache_dir, refresh=refresh)
        frames.append(df)
        provenance[name] = prov
    return pd.concat(frames, ignore_index=True), provenance
