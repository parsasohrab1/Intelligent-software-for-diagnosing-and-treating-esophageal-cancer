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
        "cholesterol_total": {"min": 0, "max": 200, "unit": "mg/dL"},
        "cholesterol_ldl": {"min": 0, "max": 100, "unit": "mg/dL"},
        "cholesterol_hdl": {"min": 40, "max": 100, "unit": "mg/dL"},
        "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
        "sodium": {"min": 135, "max": 145, "unit": "mEq/L"},
        "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
        "alkaline_phosphatase": {"min": 44, "max": 147, "unit": "U/L"},
        "glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
        "bun": {"min": 7, "max": 20, "unit": "mg/dL"},
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
        
        # Get latest imaging (and also get all imaging for comprehensive results)
        latest_imaging = db.query(ImagingData).filter(
            ImagingData.patient_id == patient.patient_id
        ).order_by(desc(ImagingData.imaging_date)).first()
        
        # Get all imaging records for this patient (limit to 10 most recent)
        all_imaging = db.query(ImagingData).filter(
            ImagingData.patient_id == patient.patient_id
        ).order_by(desc(ImagingData.imaging_date)).limit(10).all()
        
        # Get treatment data
        latest_treatment = db.query(TreatmentData).filter(
            TreatmentData.patient_id == patient.patient_id
        ).order_by(desc(TreatmentData.treatment_start_date)).first()
        
        return {
            "clinical": latest_clinical,
            "labs": latest_labs,
            "imaging": latest_imaging,
            "all_imaging": all_imaging,  # Include all imaging records
            "treatment": latest_treatment,
        }
    except (SQLAlchemyError, OperationalError, DisconnectionError) as e:
        logger.error(f"Database error in get_patient_monitoring_data: {e}")
        # Return empty data on database error
        return {
            "clinical": None,
            "labs": [],
            "imaging": None,
            "all_imaging": [],
            "treatment": None,
        }
    except Exception as e:
        logger.error(f"Error in get_patient_monitoring_data: {e}")
        return {
            "clinical": None,
            "labs": [],
            "imaging": None,
            "all_imaging": [],
            "treatment": None,
        }


@router.get("/patients/{patient_id}/monitoring", response_model=PatientMonitoringResponse)
async def get_patient_monitoring(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive monitoring data for a patient"""
    import logging
    import time
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    monitoring_data = get_patient_monitoring_data(patient, db)
    
    # Reduced logging for performance
    # logger.info(f"Monitoring data for {patient_id}: "
    #             f"clinical={monitoring_data['clinical'] is not None}, "
    #             f"labs={len(monitoring_data['labs'])}, "
    #             f"imaging={monitoring_data['imaging'] is not None}")
    
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
        
        # Temperature
        if hasattr(clinical, 'temperature') and clinical.temperature is not None:
            vital_signs.append(MonitoringParameter(
                name="Temperature",
                value=float(clinical.temperature),
                unit="°C",
                normal_range=NORMAL_RANGES["vital_signs"]["temperature"],
                status=check_parameter_status(
                    float(clinical.temperature),
                    NORMAL_RANGES["vital_signs"]["temperature"]
                ),
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Oxygen Saturation
        if hasattr(clinical, 'oxygen_saturation') and clinical.oxygen_saturation is not None:
            vital_signs.append(MonitoringParameter(
                name="Oxygen Saturation (SpO2)",
                value=float(clinical.oxygen_saturation),
                unit="%",
                normal_range=NORMAL_RANGES["vital_signs"]["oxygen_saturation"],
                status=check_parameter_status(
                    float(clinical.oxygen_saturation),
                    NORMAL_RANGES["vital_signs"]["oxygen_saturation"]
                ),
                last_updated=clinical.examination_date,
                trend=None
            ))
    
    # Build lab results - use direct fields from LabResult model
    lab_results = []
    
    # Get all lab results (not just latest) to show comprehensive data
    all_labs = monitoring_data["labs"] if monitoring_data["labs"] else []
    # Use latest lab for most recent values, but we can aggregate from multiple labs
    latest_lab = all_labs[0] if all_labs else None
    
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
        
        # Sodium
        if latest_lab.sodium is not None:
            lab_results.append(MonitoringParameter(
                name="Sodium",
                value=float(latest_lab.sodium),
                unit=NORMAL_RANGES["lab_results"]["sodium"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["sodium"],
                status=check_parameter_status(float(latest_lab.sodium), NORMAL_RANGES["lab_results"]["sodium"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # Potassium
        if latest_lab.potassium is not None:
            lab_results.append(MonitoringParameter(
                name="Potassium",
                value=float(latest_lab.potassium),
                unit=NORMAL_RANGES["lab_results"]["potassium"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["potassium"],
                status=check_parameter_status(float(latest_lab.potassium), NORMAL_RANGES["lab_results"]["potassium"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # Alkaline Phosphatase
        if latest_lab.alkaline_phosphatase is not None:
            lab_results.append(MonitoringParameter(
                name="Alkaline Phosphatase",
                value=float(latest_lab.alkaline_phosphatase),
                unit=NORMAL_RANGES["lab_results"]["alkaline_phosphatase"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["alkaline_phosphatase"],
                status=check_parameter_status(float(latest_lab.alkaline_phosphatase), NORMAL_RANGES["lab_results"]["alkaline_phosphatase"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        # Cholesterol, LDL, HDL - check if fields exist (may need to be added to model)
        # For now, we'll check if they exist using getattr
        if hasattr(latest_lab, 'cholesterol_total') and latest_lab.cholesterol_total is not None:
            lab_results.append(MonitoringParameter(
                name="Total Cholesterol",
                value=float(latest_lab.cholesterol_total),
                unit=NORMAL_RANGES["lab_results"]["cholesterol_total"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["cholesterol_total"],
                status=check_parameter_status(float(latest_lab.cholesterol_total), NORMAL_RANGES["lab_results"]["cholesterol_total"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        if hasattr(latest_lab, 'cholesterol_ldl') and latest_lab.cholesterol_ldl is not None:
            lab_results.append(MonitoringParameter(
                name="LDL Cholesterol",
                value=float(latest_lab.cholesterol_ldl),
                unit=NORMAL_RANGES["lab_results"]["cholesterol_ldl"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["cholesterol_ldl"],
                status=check_parameter_status(float(latest_lab.cholesterol_ldl), NORMAL_RANGES["lab_results"]["cholesterol_ldl"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        if hasattr(latest_lab, 'cholesterol_hdl') and latest_lab.cholesterol_hdl is not None:
            lab_results.append(MonitoringParameter(
                name="HDL Cholesterol",
                value=float(latest_lab.cholesterol_hdl),
                unit=NORMAL_RANGES["lab_results"]["cholesterol_hdl"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["cholesterol_hdl"],
                status=check_parameter_status(float(latest_lab.cholesterol_hdl), NORMAL_RANGES["lab_results"]["cholesterol_hdl"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        if hasattr(latest_lab, 'triglycerides') and latest_lab.triglycerides is not None:
            lab_results.append(MonitoringParameter(
                name="Triglycerides",
                value=float(latest_lab.triglycerides),
                unit=NORMAL_RANGES["lab_results"]["triglycerides"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["triglycerides"],
                status=check_parameter_status(float(latest_lab.triglycerides), NORMAL_RANGES["lab_results"]["triglycerides"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        if hasattr(latest_lab, 'glucose') and latest_lab.glucose is not None:
            lab_results.append(MonitoringParameter(
                name="Glucose",
                value=float(latest_lab.glucose),
                unit=NORMAL_RANGES["lab_results"]["glucose"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["glucose"],
                status=check_parameter_status(float(latest_lab.glucose), NORMAL_RANGES["lab_results"]["glucose"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
        
        if hasattr(latest_lab, 'bun') and latest_lab.bun is not None:
            lab_results.append(MonitoringParameter(
                name="BUN (Blood Urea Nitrogen)",
                value=float(latest_lab.bun),
                unit=NORMAL_RANGES["lab_results"]["bun"]["unit"],
                normal_range=NORMAL_RANGES["lab_results"]["bun"],
                status=check_parameter_status(float(latest_lab.bun), NORMAL_RANGES["lab_results"]["bun"]),
                last_updated=latest_lab.test_date,
                trend=None
            ))
    
    # Build clinical parameters
    clinical_parameters = []
    if monitoring_data["clinical"]:
        clinical = monitoring_data["clinical"]
        
        # BMI
        if clinical.bmi is not None:
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
        if clinical.weight_kg is not None:
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
        if clinical.height_cm is not None:
            clinical_parameters.append(MonitoringParameter(
                name="Height",
                value=float(clinical.height_cm),
                unit="cm",
                normal_range={"min": 150, "max": 200, "unit": "cm", "note": "Varies by patient"},
                status="normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Calculate weight loss percentage if we have historical data
        # Optimized: Only calculate if we have current weight and examination date
        if clinical.weight_kg is not None and clinical.examination_date:
            try:
                # Get previous weight if available - optimized query with filters
                previous_clinical = db.query(ClinicalData).filter(
                    ClinicalData.patient_id == patient.patient_id,
                    ClinicalData.examination_date < clinical.examination_date,
                    ClinicalData.weight_kg.isnot(None)
                ).order_by(desc(ClinicalData.examination_date)).limit(1).first()
                
                if previous_clinical and previous_clinical.weight_kg and clinical.weight_kg:
                    weight_loss = ((previous_clinical.weight_kg - clinical.weight_kg) / previous_clinical.weight_kg) * 100
                    if weight_loss > 0:
                        clinical_parameters.append(MonitoringParameter(
                            name="Weight Loss Percentage",
                            value=float(weight_loss),
                            unit="%",
                            normal_range=NORMAL_RANGES["clinical_parameters"]["weight_loss_percentage"],
                            status=check_parameter_status(weight_loss, NORMAL_RANGES["clinical_parameters"]["weight_loss_percentage"]),
                            last_updated=clinical.examination_date,
                            trend=None
                        ))
            except Exception:
                pass  # Skip if calculation fails
        
        # Tumor Stage T
        if clinical.t_stage:
            stage_value = int(clinical.t_stage.replace('T', '')) if clinical.t_stage.replace('T', '').isdigit() else None
            clinical_parameters.append(MonitoringParameter(
                name="T Stage (Tumor)",
                value=stage_value,
                unit="stage",
                normal_range={"min": 0, "max": 0, "unit": "T0", "note": "T0 = No tumor, T1-T4 = Increasing severity"},
                status="abnormal" if clinical.t_stage != "T0" else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Tumor Stage N
        if clinical.n_stage:
            stage_value = int(clinical.n_stage.replace('N', '')) if clinical.n_stage.replace('N', '').isdigit() else None
            clinical_parameters.append(MonitoringParameter(
                name="N Stage (Nodes)",
                value=stage_value,
                unit="stage",
                normal_range={"min": 0, "max": 0, "unit": "N0", "note": "N0 = No nodes, N1-N3 = Increasing involvement"},
                status="abnormal" if clinical.n_stage != "N0" else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Tumor Stage M
        if clinical.m_stage:
            stage_value = int(clinical.m_stage.replace('M', '')) if clinical.m_stage.replace('M', '').isdigit() else None
            clinical_parameters.append(MonitoringParameter(
                name="M Stage (Metastasis)",
                value=stage_value,
                unit="stage",
                normal_range={"min": 0, "max": 0, "unit": "M0", "note": "M0 = No metastasis, M1 = Metastasis present"},
                status="abnormal" if clinical.m_stage != "M0" else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Histological Grade
        if clinical.histological_grade:
            grade_value = int(clinical.histological_grade.replace('G', '')) if clinical.histological_grade.replace('G', '').isdigit() else None
            clinical_parameters.append(MonitoringParameter(
                name="Histological Grade",
                value=grade_value,
                unit="grade",
                normal_range={"min": 1, "max": 1, "unit": "G1", "note": "G1 = Well differentiated, G2-G3 = Increasing grade"},
                status="abnormal" if clinical.histological_grade not in ["G1", "GX"] else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Tumor Length (from clinical data)
        if clinical.tumor_length_cm is not None:
            clinical_parameters.append(MonitoringParameter(
                name="Tumor Length (Clinical)",
                value=float(clinical.tumor_length_cm),
                unit="cm",
                normal_range={"min": 0, "max": 0, "unit": "cm", "note": "0 = No tumor, >0 = Tumor present"},
                status="abnormal" if clinical.tumor_length_cm > 0 else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Tumor Location
        if clinical.tumor_location:
            clinical_parameters.append(MonitoringParameter(
                name="Tumor Location",
                value=None,
                unit="location",
                normal_range={"note": clinical.tumor_location},
                status="abnormal" if clinical.tumor_location else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Lymphovascular Invasion
        if clinical.lymphovascular_invasion is not None:
            clinical_parameters.append(MonitoringParameter(
                name="Lymphovascular Invasion",
                value=1.0 if clinical.lymphovascular_invasion else 0.0,
                unit="present/absent",
                normal_range={"min": 0, "max": 0, "unit": "Absent", "note": "0 = Absent, 1 = Present"},
                status="abnormal" if clinical.lymphovascular_invasion else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
        
        # Perineural Invasion
        if clinical.perineural_invasion is not None:
            clinical_parameters.append(MonitoringParameter(
                name="Perineural Invasion",
                value=1.0 if clinical.perineural_invasion else 0.0,
                unit="present/absent",
                normal_range={"min": 0, "max": 0, "unit": "Absent", "note": "0 = Absent, 1 = Present"},
                status="abnormal" if clinical.perineural_invasion else "normal",
                last_updated=clinical.examination_date,
                trend=None
            ))
    
    # Build imaging results - use latest imaging but also aggregate from all imaging
    imaging_results = []
    all_imaging = monitoring_data.get("all_imaging", [])
    
    if monitoring_data["imaging"]:
        imaging = monitoring_data["imaging"]
        # Reduced logging for performance
        # logger.info(f"Building imaging results for {patient_id}, imaging data exists, modality={imaging.imaging_modality}")
        
        # Imaging Modality
        if imaging.imaging_modality:
            imaging_results.append(MonitoringParameter(
                name="Imaging Modality",
                value=None,
                unit="type",
                normal_range={"note": imaging.imaging_modality},
                status="normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Imaging Date
        if imaging.imaging_date:
            imaging_results.append(MonitoringParameter(
                name="Imaging Date",
                value=None,
                unit="date",
                normal_range={"note": imaging.imaging_date.strftime("%Y-%m-%d") if hasattr(imaging.imaging_date, 'strftime') else str(imaging.imaging_date)},
                status="normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Tumor Length
        if imaging.tumor_length_cm is not None:
            imaging_results.append(MonitoringParameter(
                name="Tumor Length (Imaging)",
                value=float(imaging.tumor_length_cm),
                unit="cm",
                normal_range=NORMAL_RANGES["imaging"]["tumor_length"],
                status="abnormal" if imaging.tumor_length_cm > 0 else "normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Wall Thickness
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
        
        # Lymph Nodes Positive
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
        
        # Contrast Used
        if imaging.contrast_used is not None:
            imaging_results.append(MonitoringParameter(
                name="Contrast Used",
                value=1.0 if imaging.contrast_used else 0.0,
                unit="yes/no",
                normal_range={"min": 0, "max": 1, "unit": "No/Yes", "note": "0 = No contrast, 1 = Contrast used"},
                status="normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Findings (if available, show as summary) - Optimized string processing
        if imaging.findings:
            findings_str = str(imaging.findings)
            findings_summary = findings_str[:100] + "..." if len(findings_str) > 100 else findings_str
            # Optimized: Only check keywords if string is not too long
            findings_status = "normal"
            if len(findings_str) < 500:  # Only process short strings for performance
                findings_lower = findings_str.lower()
                if any(word in findings_lower for word in ["abnormal", "mass", "tumor", "lesion", "suspicious", "malignancy"]):
                    findings_status = "abnormal"
                elif any(word in findings_lower for word in ["critical", "severe", "advanced", "metastasis"]):
                    findings_status = "critical"
            
            imaging_results.append(MonitoringParameter(
                name="Imaging Findings",
                value=None,
                unit="text",
                normal_range={"note": findings_summary},
                status=findings_status,
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Impression (if available, show as summary) - Optimized string processing
        if imaging.impression:
            impression_str = str(imaging.impression)
            impression_summary = impression_str[:100] + "..." if len(impression_str) > 100 else impression_str
            # Optimized: Only check keywords if string is not too long
            impression_status = "normal"
            if len(impression_str) < 500:  # Only process short strings for performance
                impression_lower = impression_str.lower()
                if any(word in impression_lower for word in ["abnormal", "mass", "tumor", "lesion", "suspicious", "malignancy"]):
                    impression_status = "abnormal"
                elif any(word in impression_lower for word in ["critical", "severe", "advanced", "metastasis"]):
                    impression_status = "critical"
            
            imaging_results.append(MonitoringParameter(
                name="Imaging Impression",
                value=None,
                unit="text",
                normal_range={"note": impression_summary},
                status=impression_status,
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Radiologist ID (if available)
        if imaging.radiologist_id:
            imaging_results.append(MonitoringParameter(
                name="Radiologist ID",
                value=None,
                unit="id",
                normal_range={"note": str(imaging.radiologist_id)},
                status="normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
        
        # Image ID
        if imaging.image_id:
            imaging_results.append(MonitoringParameter(
                name="Image ID",
                value=float(imaging.image_id),
                unit="id",
                normal_range={"note": f"Image ID: {imaging.image_id}"},
                status="normal",
                last_updated=imaging.imaging_date,
                trend=None
            ))
    
    # If we have multiple imaging records, add summary
    if len(all_imaging) > 1:
        imaging_results.append(MonitoringParameter(
            name="Total Imaging Studies",
            value=float(len(all_imaging)),
            unit="count",
            normal_range={"note": f"Patient has {len(all_imaging)} imaging studies on record"},
            status="normal",
            last_updated=all_imaging[0].imaging_date if all_imaging else None,
            trend=None
        ))
    
    # If no imaging data but patient has cancer, recommend imaging
    if not monitoring_data["imaging"] and patient.has_cancer:
        # Reduced logging for performance
        # logger.info(f"No imaging data for {patient_id}, but patient has cancer - imaging recommended")
        imaging_results.append(MonitoringParameter(
            name="Imaging Status",
            value=None,
            unit="status",
            normal_range={"note": "No recent imaging data available. Imaging recommended for cancer patients."},
            status="missing",
            last_updated=None,
            trend=None
        ))
    
    # If no imaging data at all
    if not monitoring_data["imaging"] and not patient.has_cancer:
        # Reduced logging for performance
        # logger.info(f"No imaging data for {patient_id}")
        imaging_results.append(MonitoringParameter(
            name="Imaging Status",
            value=None,
            unit="status",
            normal_range={"note": "No imaging data available for this patient."},
            status="missing",
            last_updated=None,
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
    
    elapsed_time = time.time() - start_time
    if elapsed_time > 1.0:  # Only log if it takes more than 1 second
        logger.warning(f"Patient monitoring for {patient_id} took {elapsed_time:.2f}s")
    
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

