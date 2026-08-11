"""
CDS input data completeness validation.
Warns clinicians when patient or cancer data is missing or unreliable for CDS.
"""
from typing import Any, Dict, List, Optional


def _is_absent(data: Dict[str, Any], key: str) -> bool:
    if key not in data:
        return True
    value = data[key]
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _is_unknown(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"unknown", "n/a", "na", "not available", "—", "-"}
    return False


def _add_warning(
    warnings: List[Dict[str, str]],
    field: str,
    severity: str,
    message: str,
    message_fa: str,
) -> None:
    warnings.append(
        {
            "field": field,
            "severity": severity,
            "message": message,
            "message_fa": message_fa,
        }
    )


def validate_patient_data(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate patient_data for CDS risk prediction."""
    warnings: List[Dict[str, str]] = []
    missing_required: List[str] = []
    missing_recommended: List[str] = []

    if _is_absent(patient_data, "age"):
        missing_required.append("age")
        _add_warning(
            warnings,
            "age",
            "error",
            "Patient age is required for risk prediction.",
            "سن بیمار برای پیش‌بینی ریسک الزامی است.",
        )
    else:
        age = patient_data.get("age")
        try:
            age_num = float(age)
            if age_num < 18 or age_num > 120:
                _add_warning(
                    warnings,
                    "age",
                    "error",
                    f"Age ({age_num}) is outside the valid clinical range (18–120).",
                    f"سن ({age_num}) خارج از بازه معتبر بالینی (۱۸–۱۲۰) است.",
                )
        except (TypeError, ValueError):
            missing_required.append("age")
            _add_warning(
                warnings,
                "age",
                "error",
                "Patient age must be a valid number.",
                "سن بیمار باید یک عدد معتبر باشد.",
            )

    if _is_absent(patient_data, "gender"):
        missing_required.append("gender")
        _add_warning(
            warnings,
            "gender",
            "error",
            "Patient gender is required for risk prediction.",
            "جنسیت بیمار برای پیش‌بینی ریسک الزامی است.",
        )
    elif str(patient_data.get("gender", "")).strip() not in {"Male", "Female", "M", "F"}:
        _add_warning(
            warnings,
            "gender",
            "warning",
            "Gender should be Male or Female for accurate risk stratification.",
            "جنسیت باید Male یا Female باشد تا طبقه‌بندی ریسک دقیق‌تر شود.",
        )

    recommended_fields = {
        "bmi": (
            "BMI is missing; obesity risk factor will use a default value.",
            "شاخص توده بدنی (BMI) وارد نشده؛ عامل چاقی با مقدار پیش‌فرض محاسبه می‌شود.",
        ),
        "smoking": (
            "Smoking status not documented; assumed non-smoker.",
            "وضعیت سیگار مستند نشده؛ فرض بر غیرسیگاری است.",
        ),
        "alcohol": (
            "Alcohol use not documented; assumed no alcohol use.",
            "مصرف الکل مستند نشده؛ فرض بر عدم مصرف است.",
        ),
        "gerd": (
            "GERD history not documented; may underestimate reflux-related risk.",
            "سابقه GERD مستند نشده؛ ممکن است ریسک مرتبط با ریفلاکس کم‌برآورد شود.",
        ),
        "barretts_esophagus": (
            "Barrett's esophagus status not documented.",
            "وضعیت مری بارت مستند نشده است.",
        ),
        "family_history": (
            "Family history of cancer not documented.",
            "سابقه خانوادگی سرطان مستند نشده است.",
        ),
    }

    for field, (msg_en, msg_fa) in recommended_fields.items():
        if _is_absent(patient_data, field):
            missing_recommended.append(field)
            _add_warning(warnings, field, "warning", msg_en, msg_fa)
        elif field == "bmi":
            try:
                bmi = float(patient_data.get("bmi"))
                if bmi <= 0 or bmi > 80:
                    _add_warning(
                        warnings,
                        "bmi",
                        "warning",
                        f"BMI ({bmi}) appears invalid; verify before relying on results.",
                        f"BMI ({bmi}) نامعتبر به نظر می‌رسد؛ قبل از اتکا به نتیجه بررسی کنید.",
                    )
            except (TypeError, ValueError):
                missing_recommended.append("bmi")
                _add_warning(warnings, "bmi", "warning", recommended_fields["bmi"][0], recommended_fields["bmi"][1])

    total_checks = 2 + len(recommended_fields)
    passed = total_checks - len(missing_required) - len(missing_recommended)
    completeness_score = round(max(0.0, passed / total_checks), 2)

    is_complete = len(missing_required) == 0 and len(missing_recommended) == 0

    return {
        "is_complete": is_complete,
        "completeness_score": completeness_score,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "warnings": warnings,
        "clinical_guidance": _clinical_guidance(is_complete, missing_required, missing_recommended),
    }


def validate_cancer_data(cancer_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate cancer_data for treatment recommendation."""
    warnings: List[Dict[str, str]] = []
    missing_required: List[str] = []
    missing_recommended: List[str] = []

    if not cancer_data:
        return {
            "is_complete": False,
            "completeness_score": 0.0,
            "missing_required": ["cancer_data"],
            "missing_recommended": [],
            "warnings": [
                {
                    "field": "cancer_data",
                    "severity": "error",
                    "message": "Tumor staging data is required for treatment recommendations.",
                    "message_fa": "داده‌های staging تومور برای پیشنهاد درمان الزامی است.",
                }
            ],
            "clinical_guidance": (
                "Provide TNM staging (T, N, M) before requesting treatment recommendations. "
                "Without staging, NCCN-based regimens cannot be reliably selected."
            ),
        }

    tnm_fields = {
        "t_stage": "T stage",
        "n_stage": "N stage",
        "m_stage": "M stage",
    }
    for field, label in tnm_fields.items():
        if _is_absent(cancer_data, field):
            missing_required.append(field)
            _add_warning(
                warnings,
                field,
                "error",
                f"{label} is required for accurate treatment staging.",
                f"{label} برای staging دقیق درمان الزامی است.",
            )
        elif _is_unknown(cancer_data.get(field)):
            missing_required.append(field)
            _add_warning(
                warnings,
                field,
                "error",
                f"{label} is marked as unknown; staging must be confirmed.",
                f"{label} نامشخص است؛ staging باید تأیید شود.",
            )

    recommended = {
        "histological_grade": (
            "Histological grade not provided; prognosis estimates may be less accurate.",
            "Grade هیستولوژیک وارد نشده؛ برآورد پیش‌آگهی ممکن است کم‌دقت باشد.",
        ),
        "histology": (
            "Histology type not provided (e.g. adenocarcinoma vs squamous).",
            "نوع هیستولوژی (مثلاً آدنوکارسینوم) وارد نشده است.",
        ),
        "tumor_length_cm": (
            "Tumor length not documented.",
            "طول تومور مستند نشده است.",
        ),
        "pdl1_status": (
            "PD-L1 status unknown; immunotherapy options may not be fully evaluated.",
            "وضعیت PD-L1 نامشخص است؛ گزینه‌های ایمونوتراپی ممکن است کامل ارزیابی نشوند.",
        ),
        "tumor_location": (
            "Tumor location not specified.",
            "محل تومور مشخص نشده است.",
        ),
    }

    for field, (msg_en, msg_fa) in recommended.items():
        if _is_absent(cancer_data, field):
            missing_recommended.append(field)
            _add_warning(warnings, field, "warning", msg_en, msg_fa)
        elif _is_unknown(cancer_data.get(field)):
            missing_recommended.append(field)
            _add_warning(warnings, field, "warning", msg_en, msg_fa)

    total = len(tnm_fields) + len(recommended)
    missing_count = len(missing_required) + len(missing_recommended)
    completeness_score = round(max(0.0, (total - missing_count) / total), 2)
    is_complete = len(missing_required) == 0 and len(missing_recommended) == 0

    return {
        "is_complete": is_complete,
        "completeness_score": completeness_score,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "warnings": warnings,
        "clinical_guidance": _clinical_guidance(is_complete, missing_required, missing_recommended, context="treatment"),
    }


def validate_cds_inputs(
    patient_data: Dict[str, Any],
    cancer_data: Optional[Dict[str, Any]] = None,
    context: str = "risk_prediction",
) -> Dict[str, Any]:
    """
    Combined validation for CDS endpoints.
    context: 'risk_prediction' | 'treatment' | 'full'
    """
    patient_validation = validate_patient_data(patient_data)
    cancer_validation = validate_cancer_data(cancer_data) if context in ("treatment", "full") else None

    all_warnings = list(patient_validation["warnings"])
    if cancer_validation:
        all_warnings.extend(cancer_validation["warnings"])

    missing_required = list(patient_validation["missing_required"])
    missing_recommended = list(patient_validation["missing_recommended"])
    if cancer_validation:
        missing_required.extend(cancer_validation["missing_required"])
        missing_recommended.extend(cancer_validation["missing_recommended"])

    scores = [patient_validation["completeness_score"]]
    if cancer_validation:
        scores.append(cancer_validation["completeness_score"])
    avg_score = round(sum(scores) / len(scores), 2)

    is_complete = patient_validation["is_complete"]
    if cancer_validation:
        is_complete = is_complete and cancer_validation["is_complete"]

    reliability = "high" if is_complete else ("moderate" if not missing_required else "low")

    return {
        "is_complete": is_complete,
        "completeness_score": avg_score,
        "reliability": reliability,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "warnings": all_warnings,
        "patient_data": patient_validation,
        "cancer_data": cancer_validation,
        "clinical_guidance": _combined_guidance(patient_validation, cancer_validation, reliability),
        "prediction_reliable": reliability != "low",
    }


def _clinical_guidance(
    is_complete: bool,
    missing_required: List[str],
    missing_recommended: List[str],
    context: str = "risk",
) -> str:
    if is_complete:
        return "All key clinical fields are documented. CDS output can be used with standard confidence."

    if missing_required:
        if context == "treatment":
            return (
                "Treatment recommendations are based on incomplete staging data. "
                "Confirm TNM classification before finalizing the treatment plan."
            )
        return (
            "Risk prediction used default values for missing required fields. "
            "Results should not be used for clinical decisions until data is completed."
        )

    return (
        "Some recommended clinical fields are missing. "
        "Review warnings and supplement the patient record for higher-confidence CDS output."
    )


def _combined_guidance(
    patient_validation: Dict[str, Any],
    cancer_validation: Optional[Dict[str, Any]],
    reliability: str,
) -> str:
    if reliability == "high":
        return "Input data is complete. CDS recommendations are suitable for clinical review."

    parts = [patient_validation.get("clinical_guidance", "")]
    if cancer_validation:
        parts.append(cancer_validation.get("clinical_guidance", ""))

    if reliability == "low":
        parts.append(
            "⚠ Critical data gaps detected. Do not rely on CDS output without completing required fields."
        )
    return " ".join(p for p in parts if p)
