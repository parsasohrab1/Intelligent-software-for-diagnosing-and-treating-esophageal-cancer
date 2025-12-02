"""
Synthetic data generation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.synthetic_data_generator import EsophagealCancerSyntheticData
from app.services.data_validator import DataValidator

router = APIRouter()


class GenerateDataRequest(BaseModel):
    """Request model for data generation"""

    n_patients: int = Field(default=1000, ge=1, le=10000, description="Number of patients to generate")
    cancer_ratio: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Ratio of cancer patients"
    )
    seed: Optional[int] = Field(default=42, description="Random seed for reproducibility")
    save_to_db: bool = Field(default=False, description="Save data to database")


class GenerateDataResponse(BaseModel):
    """Response model for data generation"""

    message: str
    n_patients: int
    n_cancer: int
    n_normal: int
    generation_time: float
    validation_status: str
    quality_score: float


@router.post("/generate", response_model=GenerateDataResponse)
async def generate_synthetic_data(
    request: GenerateDataRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate synthetic esophageal cancer data"""
    import time

    start_time = time.time()

    try:
        # Initialize generator
        generator = EsophagealCancerSyntheticData(seed=request.seed)

        # Generate data
        dataset = generator.generate_all_data(
            n_patients=request.n_patients, cancer_ratio=request.cancer_ratio
        )

        # Validate data
        validator = DataValidator()
        validation_report = validator.validate_dataset(dataset)
        quality_score = validator.calculate_quality_score(validation_report)

        # Save to database if requested
        if request.save_to_db:
            background_tasks.add_task(generator.save_to_database, dataset, db)

        generation_time = time.time() - start_time

        n_cancer = len(dataset["patients"][dataset["patients"]["has_cancer"]])
        n_normal = len(dataset["patients"][~dataset["patients"]["has_cancer"]])

        return GenerateDataResponse(
            message="Synthetic data generated successfully",
            n_patients=request.n_patients,
            n_cancer=n_cancer,
            n_normal=n_normal,
            generation_time=round(generation_time, 2),
            validation_status=validation_report["overall_status"],
            quality_score=round(quality_score, 2),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating data: {str(e)}")


@router.post("/validate")
async def validate_synthetic_data(
    dataset: dict,
    db: Session = Depends(get_db),
):
    """Validate synthetic data quality"""
    try:
        validator = DataValidator()

        # Convert dict to DataFrames if needed
        import pandas as pd

        dataset_dfs = {}
        for key, value in dataset.items():
            if isinstance(value, list):
                dataset_dfs[key] = pd.DataFrame(value)
            elif isinstance(value, dict):
                dataset_dfs[key] = pd.DataFrame([value])

        validation_report = validator.validate_dataset(dataset_dfs)
        quality_score = validator.calculate_quality_score(validation_report)

        return {
            "validation_report": validation_report,
            "quality_score": round(quality_score, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating data: {str(e)}")


@router.get("/statistics")
async def get_generation_statistics(db: Session = Depends(get_db)):
    """Get statistics about generated synthetic data with caching"""
    from app.models.patient import Patient
    from app.core.cache import CacheManager
    
    cache_manager = CacheManager()
    cache_key = cache_manager.generate_key("synthetic_data", "statistics")
    
    # Try to get from cache
    cached_stats = cache_manager.get(cache_key)
    if cached_stats is not None:
        return cached_stats
    
    # Query database
    total_patients = db.query(Patient).count()
    cancer_patients = db.query(Patient).filter(Patient.has_cancer == True).count()
    normal_patients = db.query(Patient).filter(Patient.has_cancer == False).count()

    stats = {
        "total_patients": total_patients,
        "cancer_patients": cancer_patients,
        "normal_patients": normal_patients,
        "cancer_ratio": round(cancer_patients / total_patients, 3) if total_patients > 0 else 0,
    }
    
    # Cache for 15 minutes
    cache_manager.set(cache_key, stats, ttl=900)
    
    return stats

