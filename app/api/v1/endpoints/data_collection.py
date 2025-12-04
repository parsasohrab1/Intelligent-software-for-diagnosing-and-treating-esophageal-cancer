"""
Data collection endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.services.etl_pipeline import ETLPipeline
from app.services.data_quality import DataQualityAssessor
from app.services.metadata_manager import MetadataManager

router = APIRouter()


class CollectDataRequest(BaseModel):
    """Request model for data collection"""

    source: str = Field(..., description="Data source: tcga, geo, or kaggle")
    query: str = Field(
        default="esophageal cancer", description="Search query"
    )
    dataset_ids: Optional[List[str]] = Field(
        default=None, description="Specific dataset IDs to collect"
    )
    auto_download: bool = Field(
        default=False, description="Automatically download datasets"
    )


class CollectDataResponse(BaseModel):
    """Response model for data collection"""

    message: str
    source: str
    datasets_discovered: int
    datasets_processed: int
    datasets_failed: int
    output_files: List[str]


class QualityAssessmentRequest(BaseModel):
    """Request model for quality assessment"""

    dataset_path: str = Field(..., description="Path to dataset file")


@router.post("/collect", response_model=CollectDataResponse)
async def collect_data(
    request: CollectDataRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Collect data from external sources"""
    try:
        # Initialize ETL pipeline
        pipeline = ETLPipeline(
            tcga_api_key=settings.TCGA_API_KEY if hasattr(settings, "TCGA_API_KEY") else None,
            geo_api_key=settings.GEO_API_KEY if hasattr(settings, "GEO_API_KEY") else None,
            kaggle_username=settings.KAGGLE_USERNAME if hasattr(settings, "KAGGLE_USERNAME") else None,
            kaggle_key=settings.KAGGLE_KEY if hasattr(settings, "KAGGLE_KEY") else None,
        )

        # Run pipeline
        result = pipeline.run_pipeline(
            source=request.source,
            query=request.query,
            dataset_ids=request.dataset_ids,
            auto_download=request.auto_download,
        )

        return CollectDataResponse(
            message=f"Data collection from {request.source} completed",
            source=request.source,
            datasets_discovered=result["datasets_discovered"],
            datasets_processed=result["datasets_processed"],
            datasets_failed=result["datasets_failed"],
            output_files=result["output_files"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting data: {str(e)}")


@router.post("/quality-assessment")
async def assess_data_quality(request: QualityAssessmentRequest):
    """Assess quality of collected data"""
    try:
        import pandas as pd

        # Load data
        if request.dataset_path.endswith(".csv"):
            data = pd.read_csv(request.dataset_path)
        elif request.dataset_path.endswith(".parquet"):
            data = pd.read_parquet(request.dataset_path)
        else:
            raise ValueError("Unsupported file format")

        # Assess quality
        assessor = DataQualityAssessor()
        quality_report = assessor.assess_quality(data)

        return quality_report

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error assessing quality: {str(e)}"
        )


@router.get("/metadata")
async def get_metadata(
    dataset_id: Optional[str] = None,
    query: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
):
    """Get dataset metadata"""
    try:
        manager = MetadataManager()

        if dataset_id:
            metadata = manager.get_metadata(dataset_id)
            if not metadata:
                raise HTTPException(status_code=404, detail="Dataset not found")
            return metadata
        else:
            results = manager.search_metadata(
                query=query, source=source, limit=limit
            )
            return {"results": results, "count": len(results)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting metadata: {str(e)}"
        )


@router.get("/metadata/statistics")
async def get_metadata_statistics():
    """Get metadata statistics"""
    try:
        manager = MetadataManager()
        stats = manager.get_statistics()
        return stats
    except Exception as e:
        # Log error but return default empty statistics
        import logging
        logging.warning(f"Error getting metadata statistics: {str(e)}")
        # Return default empty statistics if MongoDB is not available
        return {
            "total_datasets": 0,
            "by_source": {},
            "by_data_type": {},
        }


@router.post("/deidentify")
async def deidentify_data(data: dict):
    """De-identify patient data"""
    try:
        from app.services.data_deidentifier import DataDeidentifier

        deidentifier = DataDeidentifier()
        deidentified = deidentifier.deidentify_patient_data(data)
        verification = deidentifier.verify_deidentification(deidentified)

        return {
            "deidentified_data": deidentified,
            "verification": verification,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error de-identifying data: {str(e)}"
        )

