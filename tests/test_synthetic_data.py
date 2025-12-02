"""
Tests for synthetic data generation
"""
import pytest
import pandas as pd
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.services.data_validator import DataValidator


@pytest.fixture
def generator():
    """Create a generator instance for testing"""
    return EsophagealCancerSyntheticData(seed=42)


@pytest.fixture
def validator():
    """Create a validator instance for testing"""
    return DataValidator()


def test_generator_initialization(generator):
    """Test generator initialization"""
    assert generator.seed == 42
    assert len(generator.cancer_types) > 0
    assert len(generator.clinical_parameters) > 0


def test_generate_patient_demographics(generator):
    """Test patient demographics generation"""
    df = generator.generate_patient_demographics(n_patients=100, cancer_ratio=0.3)

    assert len(df) == 100
    assert "patient_id" in df.columns
    assert "age" in df.columns
    assert "gender" in df.columns
    assert "has_cancer" in df.columns

    # Check cancer ratio
    cancer_count = len(df[df["has_cancer"] == True])
    assert 25 <= cancer_count <= 35  # Allow some variance


def test_generate_clinical_data(generator):
    """Test clinical data generation"""
    patients_df = generator.generate_patient_demographics(n_patients=50, cancer_ratio=0.3)
    clinical_df = generator.generate_clinical_data(patients_df)

    assert len(clinical_df) == len(patients_df)
    assert "patient_id" in clinical_df.columns
    assert "bmi" in clinical_df.columns
    assert "symptoms" in clinical_df.columns


def test_generate_lab_results(generator):
    """Test lab results generation"""
    patients_df = generator.generate_patient_demographics(n_patients=10, cancer_ratio=0.3)
    lab_df = generator.generate_lab_results(patients_df)

    assert len(lab_df) > 0
    assert "patient_id" in lab_df.columns
    assert "test_type" in lab_df.columns


def test_generate_genomic_data(generator):
    """Test genomic data generation"""
    patients_df = generator.generate_patient_demographics(n_patients=50, cancer_ratio=0.3)
    genomic_df = generator.generate_genomic_data(patients_df)

    # Should only have data for cancer patients
    cancer_patients = len(patients_df[patients_df["has_cancer"] == True])
    assert len(genomic_df) <= cancer_patients
    assert "patient_id" in genomic_df.columns
    assert "mutations" in genomic_df.columns


def test_generate_all_data(generator):
    """Test complete data generation"""
    dataset = generator.generate_all_data(n_patients=100, cancer_ratio=0.3)

    assert "patients" in dataset
    assert "clinical" in dataset
    assert "lab" in dataset
    assert "genomic" in dataset
    assert "imaging" in dataset
    assert "treatment" in dataset
    assert "qol" in dataset

    assert len(dataset["patients"]) == 100


def test_data_validator(validator, generator):
    """Test data validation"""
    dataset = generator.generate_all_data(n_patients=100, cancer_ratio=0.3)
    validation_report = validator.validate_dataset(dataset)

    assert "overall_status" in validation_report
    assert "detailed_results" in validation_report
    assert "errors" in validation_report
    assert "warnings" in validation_report


def test_quality_score(validator, generator):
    """Test quality score calculation"""
    dataset = generator.generate_all_data(n_patients=100, cancer_ratio=0.3)
    validation_report = validator.validate_dataset(dataset)
    quality_score = validator.calculate_quality_score(validation_report)

    assert 0 <= quality_score <= 100


def test_reproducibility():
    """Test that same seed produces same results"""
    gen1 = EsophagealCancerSyntheticData(seed=42)
    gen2 = EsophagealCancerSyntheticData(seed=42)

    df1 = gen1.generate_patient_demographics(n_patients=10, cancer_ratio=0.3)
    df2 = gen2.generate_patient_demographics(n_patients=10, cancer_ratio=0.3)

    # Check that patient IDs are the same
    assert list(df1["patient_id"]) == list(df2["patient_id"])

