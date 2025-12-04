"""
Patient monitoring endpoints for tracking vital signs, lab results, and clinical parameters
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.patient import Patient
from app.models.clinical_data import ClinicalData
from app.models.lab_results import LabResult
from app.models.imaging_data import ImagingData
from app.models.treatment_data import TreatmentData

router = APIRouter()


# Normal ranges for monitoring parameters
NORMAL_RANGES = {
    "vital_signs": {
        "blood_pressure_systolic": {"min": 90, "max": 140, "unit": "mmHg"},
        "blood_pressure_diastolic": {"min": 60, "max": 90, "unit": "mmHg"},
        "heart_rate": {"min": 60, "max": 100, "unit": "bpm"},
        "respiratory_rate": {"min": 12, "max": 20, "unit": "breaths/min"},
        "temperature": {"min": 36.1, "max": 37.2, "unit": "°C"},
        "oxygen_saturation": {"min": 95, "max": 100, "unit": "%"},
    },
    "lab_results": {
        "hemoglobin": {"min": 12.0, "max": 16.0, "unit": "g/dL", "gender_specific": True},
        "hemoglobin_male": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
        "hemoglobin_female": {"min": 12.0, "max": 15.5, "unit": "g/dL"},
        "white_blood_cell": {"min": 4.0, "max": 11.0, "unit": "×10³/μL"},
        "platelet_count": {"min": 150, "max": 450, "unit": "×10³/μL"},
        "creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
        "albumin": {"min": 3.5, "max": 5.0, "unit": "g/dL"},
        "total_bilirubin": {"min": 0.1, "max": 1.2, "unit": "mg/dL"},
        "alt": {"min": 7, "max": 56, "unit": "U/L"},
        "ast": {"min": 10, "max": 40, "unit": "U/L"},
        "c_reactive_protein": {"min": 0, "max": 3.0, "unit": "mg/L"},
        "tumor_marker_cea": {"min": 0, "max": 3.0, "unit": "ng/mL"},
        "tumor_marker_ca19_9": {"min": 0, "max": 37, "unit": "U/mL"},
    },
    "clinical_parameters": {
        "bmi": {"min": 18.5, "max": 24.9, "unit": "kg/m²"},
        "weight_loss_percentage": {"min": 0, "max": 5, "unit": "%"},
        "ecog_performance_status": {"min": 0, "max": 1, "unit": "score"},
        "pain_score": {"min": 0, "max": 3, "unit": "0-10 scale"},
    },
    "imaging": {
        "tumor_length": {"min": 0, "max": 0, "unit": "cm", "note": "Any value > 0 indicates abnormality"},
        "wall_thickness": {"min": 0.3, "max": 0.5, "unit": "cm"},
        "lymph_nodes_positive": {"min": 0, "max": 0, "unit": "count", "note": "0 is normal"},
    },
}


class MonitoringParameter(BaseModel):
    """Model for a monitoring parameter"""
    name: str
    value: Optional[float]
    unit: str
    normal_range: Dict[str, Any]
    status: str  # "normal", "abnormal", "critical", "missing"
    last_updated: Optional[date]
    trend: Optional[str]  # "increasing", "decreasing", "stable"


class PatientMonitoringResponse(BaseModel):
    """Response model for patient monitoring"""
    patient_id: str
    patient_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    has_cancer: bool
    monitoring_date: date
    vital_signs: List[MonitoringParameter]
    lab_results: List[MonitoringParameter]
    clinical_parameters: List[MonitoringParameter]
    imaging_results: List[MonitoringParameter]
    overall_status: str  # "stable", "monitoring_required", "intervention_needed", "critical"
    alerts: List[str]


def check_parameter_status(value: Optional[float], normal_range: Dict[str, Any]) -> str:
    """Check if parameter value is within normal range"""
    if value is None:
        return "missing"
    
    min_val = normal_range.get("min")
    max_val = normal_range.get("max")
    
    if min_val is None and max_val is None:
        return "normal"  # No range specified
    
    if min_val is not None and value < min_val:
        if value < min_val * 0.7:  # Critical if 30% below minimum
            return "critical"
        return "abnormal"
    
    if max_val is not None and value > max_val:
        if value > max_val * 1.3:  # Critical if 30% above maximum
            return "critical"
        return "abnormal"
    
    return "normal"


def get_patient_monitoring_data(patient: Patient, db: Session) -> Dict[str, Any]:
    """Get all monitoring data for a patient"""
    import logging
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get latest clinical data - use examination_date (not record_date)
        # Handle null dates by ordering and filtering
        latest_clinical = db.query(ClinicalData).filter(
            ClinicalData.patient_id == patient.patient_id
        ).order_by(desc(ClinicalData.examination_date)).first()
        
        # Get latest lab results
        latest_labs = db.query(LabResult).filter(
            LabResult.patient_id == patient.patient_id
        ).order_by(desc(LabResult.test_date)).limit(10).all()
        
        # Get latest imaging
        latest_imaging = db.query(ImagingData).filter(
            ImagingData.patient_id == patient.patient_id
        ).order_by(desc(ImagingData.imaging_date)).first()
        
        # Get treatment data
        latest_treatment = db.query(TreatmentData).filter(
            TreatmentData.patient_id == patient.patient_id
        ).order_by(desc(TreatmentData.treatment_start_date)).first()
        
        return {
            "clinical": latest_clinical,
            "labs": latest_labs,
            "imaging": latest_imaging,
            "treatment": latest_treatment,
        }
    except (SQLAlchemyError, OperationalError, DisconnectionError) as e:
        logger.error(f"Database error in get_patient_monitoring_data: {e}")
        # Return empty data on database error
        return {
            "clinical": None,
            "labs": [],
            "imaging": None,
            "treatment": None,
        }
    except Exception as e:
        logger.error(f"Error in get_patient_monitoring_data: {e}")
        return {
            "clinical": None,
            "labs": [],
            "imaging": None,
            "treatment": None,
        }


@router.get("/patients/{patient_id}/monitoring", response_model=PatientMonitoringResponse)
async def get_patient_monitoring(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive monitoring data for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    monitoring_data = get_patient_monitoring_data(patient, db)
    
    # Build vital signs
    vital_signs = []
    if monitoring_data["clinical"]:
        clinical = monitoring_data["clinical"]
        
        # Blood pressure (systolic)
        if clinical.systolic_bp:
            vital_signs.append(MonitoringParameter(
                name="Blood Pressure (Systolic)",
                value=float(clinical.systolic_bp),
                unit="mmHg",
                normal_range=NORMAL_RANGES["vital_signs"]["blood_pressure_systolic"],
                status=check_parameter_status(
                    float(clinical.systolic_bp),
                    NORMAL_RANGES["vital_signs"]["blood_pressure_systolic"]
                ),
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Blood pressure (diastolic)
        if clinical.diastolic_bp:
            vital_signs.append(MonitoringParameter(
                name="Blood Pressure (Diastolic)",
                value=float(clinical.diastolic_bp),
                unit="mmHg",
                normal_range=NORMAL_RANGES["vital_signs"]["blood_pressure_diastolic"],
                status=check_parameter_status(
                    float(clinical.diastolic_bp),
                    NORMAL_RANGES["vital_signs"]["blood_pressure_diastolic"]
                ),
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Heart rate
        if clinical.heart_rate:
            vital_signs.append(MonitoringParameter(
                name="Heart Rate",
                value=float(clinical.heart_rate),
                unit="bpm",
                normal_range=NORMAL_RANGES["vital_signs"]["heart_rate"],
                status=check_parameter_status(
                    float(clinical.heart_rate),
                    NORMAL_RANGES["vital_signs"]["heart_rate"]
                ),
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Respiratory rate
        if clinical.respiratory_rate:
            vital_signs.append(MonitoringParameter(
                name="Respiratory Rate",
                value=float(clinical.respiratory_rate),
                unit="breaths/min",
                normal_range=NORMAL_RANGES["vital_signs"]["respiratory_rate"],
                status=check_parameter_status(
                    float(clinical.respiratory_rate),
                    NORMAL_RANGES["vital_signs"]["respiratory_rate"]
                ),
                last_updated=clinical.examination_date,
                trend=None
            ))
    
    # Build lab results - use direct fields from LabResult model
    lab_results = []
    
    # Get latest lab result
    latest_lab = monitoring_data["labs"][0] if monitoring_data["labs"] else None
    
    if latest_lab:
        # Hemoglobin
        if latest_lab.hemoglobin is not None:
            # Gender-specific range
            if patient.gender and patient.gender.lower() == "male":
                normal_range = NORMAL_RANGES["lab_results"]["hemoglobin_male"]
            else:
                normal_range = NORMAL_RANGES["lab_results"]["hemoglobin_female"]
            
            lab_results.append(MonitoringParameter(
                name="Hemoglobin",
                value=float(latest_lab.hemoglobin),
                unit=normal_range["unit"],
                normal_range=normal_range,
                status=check_parameter_status(latest_lab.hemoglobin, normal_range),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # White Blood Cell Count
        if latest_lab.wbc_count is not None:
            lab_results.append(MonitoringParameter(
                name="White Blood Cell Count",
                value=float(latest_lab.wbc_count),
                unit=NORMAL_RANGES["lab_results"]["white_blood_cell"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["white_blood_cell"],
                status=check_parameter_status(latest_lab.wbc_count, NORMAL_RANGES["lab_results"]["white_blood_cell"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # Platelet Count
        if latest_lab.platelet_count is not None:
            lab_results.append(MonitoringParameter(
                name="Platelet Count",
                value=float(latest_lab.platelet_count),
                unit=NORMAL_RANGES["lab_results"]["platelet_count"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["platelet_count"],
                status=check_parameter_status(float(latest_lab.platelet_count), NORMAL_RANGES["lab_results"]["platelet_count"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # Creatinine
        if latest_lab.creatinine is not None:
            lab_results.append(MonitoringParameter(
                name="Creatinine",
                value=float(latest_lab.creatinine),
                unit=NORMAL_RANGES["lab_results"]["creatinine"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["creatinine"],
                status=check_parameter_status(latest_lab.creatinine, NORMAL_RANGES["lab_results"]["creatinine"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # Albumin
        if latest_lab.albumin is not None:
            lab_results.append(MonitoringParameter(
                name="Albumin",
                value=float(latest_lab.albumin),
                unit=NORMAL_RANGES["lab_results"]["albumin"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["albumin"],
                status=check_parameter_status(latest_lab.albumin, NORMAL_RANGES["lab_results"]["albumin"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # AST
        if latest_lab.ast is not None:
            lab_results.append(MonitoringParameter(
                name="AST (Aspartate Aminotransferase)",
                value=float(latest_lab.ast),
                unit=NORMAL_RANGES["lab_results"]["ast"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["ast"],
                status=check_parameter_status(float(latest_lab.ast), NORMAL_RANGES["lab_results"]["ast"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # ALT
        if latest_lab.alt is not None:
            lab_results.append(MonitoringParameter(
                name="ALT (Alanine Aminotransferase)",
                value=float(latest_lab.alt),
                unit=NORMAL_RANGES["lab_results"]["alt"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["alt"],
                status=check_parameter_status(float(latest_lab.alt), NORMAL_RANGES["lab_results"]["alt"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # CEA (Tumor Marker)
        if latest_lab.cea is not None:
            lab_results.append(MonitoringParameter(
                name="CEA (Carcinoembryonic Antigen)",
                value=float(latest_lab.cea),
                unit=NORMAL_RANGES["lab_results"]["tumor_marker_cea"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["tumor_marker_cea"],
                status=check_parameter_status(latest_lab.cea, NORMAL_RANGES["lab_results"]["tumor_marker_cea"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # CA19-9 (Tumor Marker)
        if latest_lab.ca19_9 is not None:
            lab_results.append(MonitoringParameter(
                name="CA19-9 (Tumor Marker)",
                value=float(latest_lab.ca19_9),
                unit=NORMAL_RANGES["lab_results"]["tumor_marker_ca19_9"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["tumor_marker_ca19_9"],
                status=check_parameter_status(latest_lab.ca19_9, NORMAL_RANGES["lab_results"]["tumor_marker_ca19_9"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # CRP (C-Reactive Protein)
        if latest_lab.crp is not None:
            lab_results.append(MonitoringParameter(
                name="C-Reactive Protein (CRP)",
                value=float(latest_lab.crp),
                unit=NORMAL_RANGES["lab_results"]["c_reactive_protein"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["c_reactive_protein"],
                status=check_parameter_status(latest_lab.crp, NORMAL_RANGES["lab_results"]["c_reactive_protein"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
    
    # Build clinical parameters
    clinical_parameters = []
    if monitoring_data["clinical"]:
        clinical = monitoring_data["clinical"]
        
        # BMI
        if clinical.bmi:
            clinical_parameters.append(MonitoringParameter(
                name="BMI (Body Mass Index)",
                value=float(clinical.bmi),
                unit=NORMAL_RANGES["clinical_parameters"]["bmi"]["unit"],
                normal_range=NORMAL_RANGES["clinical_parameters"]["bmi"],
                status=check_parameter_status(clinical.bmi, NORMAL_RANGES["clinical_parameters"]["bmi"]),
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Weight
        if clinical.weight_kg:
            clinical_parameters.append(MonitoringParameter(
                name="Weight",
                value=float(clinical.weight_kg),
                unit="kg",
                normal_range={"min": 50, "max": 120, "unit": "kg", "note": "Varies by patient"},
                status="normal",  # Weight needs context (height, baseline)
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Height
        if clinical.height_cm:
            clinical_parameters.append(MonitoringParameter(
                name="Height",
                value=float(clinical.height_cm),
                unit="cm",
                normal_range={"min": 150, "max": 200, "unit": "cm", "note": "Varies by patient"},
                status="normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Tumor Stage (if available)
        if clinical.t_stage:
            clinical_parameters.append(MonitoringParameter(
                name="T Stage",
                value=None,
                unit="stage",
                normal_range={"min": 0, "max": 0, "unit": "T0", "note": "T0 = No tumor, T1-T4 = Increasing severity"},
                status="abnormal" if clinical.t_stage != "T0" else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
    
    # Build imaging results
    imaging_results = []
    if monitoring_data["imaging"]:
        imaging = monitoring_data["imaging"]
        
        if imaging.tumor_length_cm is not None:
            imaging_results.append(MonitoringParameter(
                name="Tumor Length",
                value=float(imaging.tumor_length_cm),
                unit="cm",
                normal_range=NORMAL_RANGES["imaging"]["tumor_length"],
                status="abnormal" if imaging.tumor_length_cm > 0 else "normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        if imaging.wall_thickness_cm is not None:
            imaging_results.append(MonitoringParameter(
                name="Wall Thickness",
                value=float(imaging.wall_thickness_cm),
                unit="cm",
                normal_range=NORMAL_RANGES["imaging"]["wall_thickness"],
                status=check_parameter_status(
                    imaging.wall_thickness_cm,
                    NORMAL_RANGES["imaging"]["wall_thickness"]
                ),
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        if imaging.lymph_nodes_positive is not None:
            imaging_results.append(MonitoringParameter(
                name="Lymph Nodes Positive",
                value=float(imaging.lymph_nodes_positive),
                unit="count",
                normal_range=NORMAL_RANGES["imaging"]["lymph_nodes_positive"],
                status="abnormal" if imaging.lymph_nodes_positive > 0 else "normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
    
    # Determine overall status
    all_parameters = vital_signs + lab_results + clinical_parameters + imaging_results
    critical_count = sum(1 for p in all_parameters if p.status == "critical")
    abnormal_count = sum(1 for p in all_parameters if p.status == "abnormal")
    
    if critical_count > 0:
        overall_status = "critical"
    elif abnormal_count > 2:
        overall_status = "intervention_needed"
    elif abnormal_count > 0:
        overall_status = "monitoring_required"
    else:
        overall_status = "stable"
    
    # Generate alerts
    alerts = []
    for param in all_parameters:
        if param.status == "critical":
            alerts.append(f"⚠️ CRITICAL: {param.name} is outside normal range")
        elif param.status == "abnormal":
            alerts.append(f"⚠️ {param.name} requires attention")
    
    return PatientMonitoringResponse(
        patient_id=patient.patient_id,
        patient_name=getattr(patient, 'name', None),
        age=patient.age,
        gender=patient.gender,
        has_cancer=patient.has_cancer,
        monitoring_date=date.today(),
        vital_signs=vital_signs,
        lab_results=lab_results,
        clinical_parameters=clinical_parameters,
        imaging_results=imaging_results,
        overall_status=overall_status,
        alerts=alerts
    )


@router.get("/patients/monitoring/all", response_model=List[PatientMonitoringResponse])
async def get_all_patients_monitoring(
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, ge=1, le=50000),
    db: Session = Depends(get_db)
):
    """Get monitoring data for all patients"""
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    results = []
    for patient in patients:
        try:
            monitoring = await get_patient_monitoring(patient.patient_id, db)
            results.append(monitoring)
        except Exception as e:
            # Skip patients with errors
            continue
    
    return results


@router.get("/monitoring/normal-ranges", response_model=Dict[str, Any])
async def get_normal_ranges():
    """Get all normal ranges for monitoring parameters"""
    return NORMAL_RANGES

