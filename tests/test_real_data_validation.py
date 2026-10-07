"""
Unit tests for the real-data validation stack.

These are deliberately network-free and import only numpy/pandas/scipy, so they
run without the heavy ML dependencies. Run standalone with:

    pytest --noconftest tests/test_real_data_validation.py
"""
import math

import numpy as np
import pandas as pd
import pytest

from app.services.real_data.cohort import apply_eligibility, finalize_cohort
from app.services.real_data.normalize import (
    histology_from_text,
    normalize_m,
    normalize_n,
    normalize_t,
    parse_tnm_string,
    stage_group,
)
from app.services.real_data.sources import (
    parse_cbioportal_icgc_escc,
    parse_gdc_cases,
    parse_geo_series_matrix_header,
)
from app.services.validation.survival_metrics import (
    bootstrap_ci,
    concordance_index,
    kaplan_meier,
    km_survival_at,
    logrank_test,
    median_follow_up_reverse_km,
    time_dependent_auc,
)


class TestNormalize:
    def test_tnm_variants(self):
        assert normalize_t("T4a") == "T4"
        assert normalize_t("TX") == "" and normalize_t(None) == ""
        assert normalize_n("N2") == "N2" and normalize_n("NX") == ""
        assert normalize_m("M1a") == "M1" and normalize_m("MX") == "" and normalize_m("Unknown") == ""

    def test_stage_group(self):
        assert stage_group("Stage IIIB") == "III"
        assert stage_group("IVA") == "IV"
        assert stage_group("Stage IB") == "I"
        assert stage_group("IIA") == "II"
        assert stage_group("Unknown") == "" and stage_group(None) == ""

    def test_tnm_string_and_histology(self):
        assert parse_tnm_string("T3N1M0") == ("T3", "N1", "M0")
        assert parse_tnm_string("garbage") == ("", "", "")
        assert histology_from_text("Squamous cell carcinoma, NOS") == "ESCC"
        assert histology_from_text("Adenocarcinoma, NOS") == "EAC"


class TestMetricsKnownValues:
    def test_c_index_perfect_reversed_constant(self):
        t, e = [1, 2, 3, 4], [1, 1, 1, 1]
        assert concordance_index(t, e, [4, 3, 2, 1]) == 1.0
        assert concordance_index(t, e, [1, 2, 3, 4]) == 0.0
        assert concordance_index(t, e, [5, 5, 5, 5]) == 0.5

    def test_c_index_no_comparable_pairs_is_nan(self):
        assert math.isnan(concordance_index([1, 2], [0, 0], [1, 2]))

    def test_c_index_strata_only_compares_within_stratum(self):
        # Within each stratum the ordering is perfect; across strata it is adversarial.
        t = [1, 2, 10, 20]
        e = [1, 1, 1, 1]
        risk = [4, 3, 2, 1]
        strata = ["a", "a", "b", "b"]
        assert concordance_index(t, e, risk) == 1.0
        assert concordance_index(t, e, [4, 3, 6, 5], strata) == 1.0
        assert concordance_index(t, e, [4, 3, 6, 5]) < 1.0

    def test_kaplan_meier_hand_computed(self):
        times, surv = kaplan_meier([1, 2, 3], [1, 1, 1])
        assert np.allclose(surv, [2 / 3, 1 / 3, 0.0])
        # with censoring: S(1)=3/4, S(3)=3/4*1/2
        assert km_survival_at([1, 2, 3, 4], [1, 0, 1, 0], 1) == pytest.approx(0.75)
        assert km_survival_at([1, 2, 3, 4], [1, 0, 1, 0], 3) == pytest.approx(0.375)
        assert math.isnan(km_survival_at([1, 2, 3, 4], [1, 0, 1, 0], 10))  # beyond follow-up

    def test_logrank_hand_computed_two_groups(self):
        # A: t=1,2  B: t=3,4 (all events) -> chi2 = 1.1667^2 / 0.4722 = 2.882
        res = logrank_test([1, 2, 3, 4], [1, 1, 1, 1], ["A", "A", "B", "B"])
        assert res["df"] == 1
        assert res["chi2"] == pytest.approx(2.8824, abs=1e-3)

    def test_logrank_separated_vs_identical(self):
        rng = np.random.default_rng(0)
        a = rng.exponential(10, 80)
        b = rng.exponential(40, 80)
        t = np.concatenate([a, b])
        g = ["a"] * 80 + ["b"] * 80
        assert logrank_test(t, np.ones(160), g)["p_value"] < 0.001
        same = rng.exponential(10, 160)
        assert logrank_test(same, np.ones(160), g)["p_value"] > 0.05

    def test_time_dependent_auc(self):
        t, e = [1, 2, 8, 9], [1, 1, 0, 0]
        res = time_dependent_auc(t, e, [4, 3, 2, 1], horizon_days=5)
        assert res["auc"] == 1.0 and res["n_cases"] == 2 and res["n_controls"] == 2

    def test_median_follow_up_reverse_km(self):
        t = np.arange(1, 21)
        assert median_follow_up_reverse_km(t, np.zeros(20, int)) > 0  # all censored

    def test_bootstrap_ci_contains_point_estimate_and_is_reproducible(self):
        rng = np.random.default_rng(1)
        t = rng.exponential(10, 120)
        e = (rng.random(120) < 0.7).astype(int)
        risk = -t + rng.normal(0, 3, 120)  # informative
        point = concordance_index(t, e, risk)
        ci1 = bootstrap_ci(concordance_index, [t, e, risk], n_boot=300, seed=7)
        ci2 = bootstrap_ci(concordance_index, [t, e, risk], n_boot=300, seed=7)
        assert ci1 == ci2
        assert ci1["lower"] < point < ci1["upper"]


class TestParsers:
    def test_parse_gdc_cases_uses_primary_diagnosis_and_follow_up(self):
        hits = [
            {
                "submitter_id": "TCGA-AA-0001",
                "demographic": {"vital_status": "Dead", "days_to_death": 400, "age_at_index": 70, "sex_at_birth": "male"},
                "diagnoses": [
                    {"diagnosis_is_primary_disease": False, "ajcc_pathologic_t": "T1"},  # prior primary: ignored
                    {
                        "diagnosis_is_primary_disease": True,
                        "primary_diagnosis": "Adenocarcinoma, NOS",
                        "ajcc_pathologic_t": "T3",
                        "ajcc_pathologic_n": "N1",
                        "ajcc_pathologic_m": "M0",
                        "ajcc_pathologic_stage": "Stage IIIA",
                    },
                ],
                "follow_ups": [],
            },
            {
                "submitter_id": "TCGA-AA-0002",
                "demographic": {"vital_status": "Alive", "age_at_index": 55, "sex_at_birth": "female"},
                "diagnoses": [{"diagnosis_is_primary_disease": True, "days_to_last_follow_up": 100, "primary_diagnosis": "Squamous cell carcinoma, NOS"}],
                "follow_ups": [{"days_to_follow_up": 250}],
            },
        ]
        df = parse_gdc_cases(hits)
        a, b = df.iloc[0], df.iloc[1]
        assert (a.t_stage, a.n_stage, a.m_stage, a.stage_group, a.histology) == ("T3", "N1", "M0", "III", "EAC")
        assert (a.time_days, a.event) == (400, 1)
        assert (b.time_days, b.event, b.histology) == (250, 0, "ESCC")  # max of follow-ups

    def test_parse_geo_header_one_row_per_patient(self):
        def line(key, vals):
            return "!Sample_characteristics_ch1\t" + "\t".join(f'"{key}: {v}"' for v in vals)

        text = "\n".join(
            [
                line("patient id", ["ec1", "ec1", "ec2", "ec2"]),
                line("age", [60, 60, 70, 70]),
                line("Sex", ["male", "male", "female", "female"]),
                line("t stage", ["T3", "T3", "T2", "T2"]),
                line("n stage", ["N1", "N1", "N0", "N0"]),
                line("tnm stage", ["III", "III", "II", "II"]),
                line("death at fu", ["yes", "yes", "no", "no"]),
                line("survival time(months)", [10, 10, 30, 30]),
            ]
        )
        df = parse_geo_series_matrix_header(text)
        assert list(df.patient_id) == ["ec1", "ec2"]
        assert list(df.event) == [1, 0]
        assert df.time_days.iloc[0] == pytest.approx(10 * 30.4375)
        assert list(df.stage_group) == ["III", "II"]

    def test_parse_cbioportal_icgc(self):
        patients = [
            {"patientId": "P1", "clinicalAttributeId": "AGE", "value": "60"},
            {"patientId": "P1", "clinicalAttributeId": "SEX", "value": "Male"},
            {"patientId": "P1", "clinicalAttributeId": "OS_MONTHS", "value": "12.5"},
            {"patientId": "P1", "clinicalAttributeId": "OS_STATUS", "value": "1:DECEASED"},
        ]
        samples = [
            {"patientId": "P1", "clinicalAttributeId": "TNM", "value": "T3N1M0"},
            {"patientId": "P1", "clinicalAttributeId": "TUMOR_STAGE", "value": "IIIA"},
        ]
        df = parse_cbioportal_icgc_escc(patients, samples)
        r = df.iloc[0]
        assert (r.t_stage, r.n_stage, r.m_stage, r.stage_group, r.event) == ("T3", "N1", "M0", "III", 1)


class TestEligibility:
    def test_excludes_invalid_follow_up_and_reports_flow(self):
        df = finalize_cohort(
            [
                {"cohort": "X", "patient_id": "1", "time_days": 100, "event": 1},
                {"cohort": "X", "patient_id": "2", "time_days": 0, "event": 0},
                {"cohort": "X", "patient_id": "3", "time_days": None, "event": 1},
                {"cohort": "X", "patient_id": "4", "time_days": 50, "event": None},
            ]
        )
        elig, flow = apply_eligibility(df)
        assert list(elig.patient_id) == ["1"]
        assert flow["X"]["excluded_invalid_follow_up_time"] == 2
        assert flow["X"]["excluded_missing_vital_status"] == 1
        assert flow["X"]["n_eligible"] == 1 and flow["X"]["n_events"] == 1
