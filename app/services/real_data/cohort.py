"""
Unified real-world cohort schema.

Every source (GDC, GEO, cBioPortal) is reduced to the same columns so the
validation engine never needs to know where a patient came from:

    cohort, patient_id, age, sex, histology,
    t_stage, n_stage, m_stage, stage_group,
    time_days, event            (event: 1 = death, 0 = censored)
"""
import pandas as pd

COHORT_COLUMNS = [
    "cohort",
    "patient_id",
    "age",
    "sex",
    "histology",
    "t_stage",
    "n_stage",
    "m_stage",
    "stage_group",
    "time_days",
    "event",
]

DAYS_PER_MONTH = 30.4375


def empty_cohort() -> pd.DataFrame:
    return pd.DataFrame(columns=COHORT_COLUMNS)


def finalize_cohort(rows: list) -> pd.DataFrame:
    """Build a DataFrame with the unified columns from a list of dict rows."""
    df = pd.DataFrame(rows)
    for col in COHORT_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COHORT_COLUMNS].copy()
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["time_days"] = pd.to_numeric(df["time_days"], errors="coerce")
    df["event"] = pd.to_numeric(df["event"], errors="coerce")
    return df.reset_index(drop=True)


def apply_eligibility(df: pd.DataFrame) -> tuple:
    """Apply the protocol's inclusion criteria.

    Returns (eligible_df, flow) where ``flow`` is a CONSORT-style dict of how
    many patients were excluded and why, per cohort.
    """
    flow = {}
    keep_masks = []
    for cohort, sub in df.groupby("cohort", sort=False):
        invalid_time = sub["time_days"].isna() | (sub["time_days"] <= 0)
        invalid_event = sub["event"].isna()
        keep = ~(invalid_time | invalid_event)
        flow[cohort] = {
            "n_source": int(len(sub)),
            "excluded_invalid_follow_up_time": int(invalid_time.sum()),
            "excluded_missing_vital_status": int((invalid_event & ~invalid_time).sum()),
            "n_eligible": int(keep.sum()),
            "n_events": int(sub.loc[keep, "event"].sum()),
        }
        keep_masks.append(keep)
    mask = pd.concat(keep_masks).reindex(df.index) if keep_masks else pd.Series(dtype=bool)
    return df[mask].reset_index(drop=True), flow
