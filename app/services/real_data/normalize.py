"""
Pure helpers that normalise heterogeneous real-world clinical vocabularies
(TCGA/GDC, GEO, cBioPortal) into the vocabulary the CDS services expect.

Kept free of I/O so it can be unit-tested without network access.
"""
import re
from typing import Optional


def normalize_t(value) -> str:
    """'T4a' -> 'T4', 'T1b' -> 'T1'; unknown/'TX'/'T0'/None -> ''."""
    m = re.match(r"^\s*T([1-4])", str(value or "").upper())
    return f"T{m.group(1)}" if m else ""


def normalize_n(value) -> str:
    """'N2' -> 'N2'; 'NX'/None -> ''."""
    m = re.match(r"^\s*N([0-3])", str(value or "").upper())
    return f"N{m.group(1)}" if m else ""


def normalize_m(value) -> str:
    """'M1a' -> 'M1'; 'MX'/'Unknown'/None -> ''."""
    m = re.match(r"^\s*M([01])", str(value or "").upper())
    return f"M{m.group(1)}" if m else ""


def stage_group(value) -> str:
    """'Stage IIIB' / 'IIIB' / 'III' -> 'III'; unknown -> ''."""
    s = str(value or "").upper().replace("STAGE", "").strip()
    m = re.match(r"^(IV|III|II|I)(?=[ABC]?$)", s)
    return m.group(1) if m else ""


def parse_tnm_string(value) -> tuple:
    """'T3N1M0' -> ('T3', 'N1', 'M0'); anything unparsable -> ('', '', '')."""
    s = str(value or "").upper()
    t = re.search(r"T([1-4])", s)
    n = re.search(r"N([0-3])", s)
    m = re.search(r"M([01])", s)
    return (
        f"T{t.group(1)}" if t else "",
        f"N{n.group(1)}" if n else "",
        f"M{m.group(1)}" if m else "",
    )


def stage_group_to_ordinal(group: str) -> Optional[int]:
    return {"I": 1, "II": 2, "III": 3, "IV": 4}.get(group)


def normalize_sex(value) -> str:
    s = str(value or "").strip().lower()
    if s in ("male", "m"):
        return "Male"
    if s in ("female", "f"):
        return "Female"
    return ""


def histology_from_text(value) -> str:
    """Coarse histology: 'ESCC', 'EAC' or ''."""
    s = str(value or "").lower()
    if "squamous" in s:
        return "ESCC"
    if "adenocarcinoma" in s or "adenoca" in s:
        return "EAC"
    return ""
