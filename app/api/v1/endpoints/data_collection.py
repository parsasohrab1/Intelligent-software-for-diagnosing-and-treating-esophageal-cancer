"""
Data collection endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Limit the maximum allowed limit to prevent timeouts and memory issues
        max_limit = 1000
        effective_limit = min(limit, max_limit) if limit > max_limit else limit
        
        if limit > max_limit:
            logger.warning(f"Metadata query limit reduced from {limit} to {effective_limit} to prevent timeouts")
        
        manager = MetadataManager()

        if dataset_id:
            metadata = manager.get_metadata(dataset_id)
            if not metadata:
                raise HTTPException(status_code=404, detail="Dataset not found")
            return metadata
        else:
            # Use search_metadata with limited results
            results = manager.search_metadata(
                query=query, source=source, limit=effective_limit
            )
            return {"results": results, "count": len(results), "limit_applied": effective_limit, "original_limit": limit if limit > max_limit else None}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metadata: {str(e)}", exc_info=True)
        # Return empty results instead of 500 error for better UX
        return {"results": [], "count": 0, "error": "Failed to load metadata. Please try with a smaller limit or check backend logs."}


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


@router.get("/collected-files")
async def list_collected_files(source: Optional[str] = None):
    """List all collected data files from the collected_data directory (recursively)"""
    import os
    from pathlib import Path
    from datetime import datetime
    
    try:
        collected_data_dir = Path("collected_data")
        
        if not collected_data_dir.exists():
            return {"files": [], "count": 0}
        
        files_list = []
        
        # Recursively search for CSV and Parquet files
        # If source is specified, only search in that subdirectory
        if source:
            search_dirs = [collected_data_dir / source.lower()]
        else:
            # Search in all subdirectories and root
            search_dirs = [collected_data_dir]
            # Also search in known source directories
            for src in ["tcga", "geo", "kaggle"]:
                src_dir = collected_data_dir / src
                if src_dir.exists():
                    search_dirs.append(src_dir)
        
        # Remove duplicates
        search_dirs = list(set(search_dirs))
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            # Find all CSV and Parquet files recursively
            for file_path in search_dir.rglob("*.csv"):
                try:
                    # Determine source from path
                    rel_path = file_path.relative_to(collected_data_dir)
                    path_parts = rel_path.parts
                    file_source = path_parts[0] if len(path_parts) > 1 else "unknown"
                    
                    file_info = {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "source": file_source,
                        "size_bytes": file_path.stat().st_size,
                        "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                        "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    }
                    files_list.append(file_info)
                except Exception as file_err:
                    import logging
                    logging.warning(f"Error processing file {file_path}: {file_err}")
                    continue
            
            for file_path in search_dir.rglob("*.parquet"):
                try:
                    # Determine source from path
                    rel_path = file_path.relative_to(collected_data_dir)
                    path_parts = rel_path.parts
                    file_source = path_parts[0] if len(path_parts) > 1 else "unknown"
                    
                    file_info = {
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "source": file_source,
                        "size_bytes": file_path.stat().st_size,
                        "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                        "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    }
                    files_list.append(file_info)
                except Exception as file_err:
                    import logging
                    logging.warning(f"Error processing file {file_path}: {file_err}")
                    continue
        
        return {"files": files_list, "count": len(files_list)}
        
    except Exception as e:
        import logging
        logging.error(f"Error listing collected files: {e}")
        return {"files": [], "count": 0}


@router.get("/aggregated-statistics")
async def get_aggregated_statistics():
    """Get comprehensive aggregated statistics for all collected data"""
    from pathlib import Path
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize default values
        total_size_bytes = 0
        total_size_mb = 0
        sources_count = {}
        files_by_source = {}
        files_by_type = {"csv": 0, "parquet": 0}
        latest_collection_date = None
        
        # Get metadata statistics (with timeout handling)
        metadata_stats = {}
        try:
            manager = MetadataManager()
            metadata_stats = manager.get_statistics() or {}
        except Exception as e:
            logger.warning(f"Could not get metadata statistics: {e}")
            metadata_stats = {"total_datasets": 0, "by_source": {}, "by_data_type": {}}
        
        # Get all files
        collected_data_dir = Path("collected_data")
        
        if collected_data_dir.exists():
            sources = ["tcga", "geo", "kaggle"]
            for src in sources:
                source_dir = collected_data_dir / src
                if not source_dir.exists():
                    continue
                
                source_count = 0
                source_size = 0
                
                try:
                    # Count CSV files
                    csv_files = list(source_dir.glob("*.csv"))
                    for file_path in csv_files:
                        try:
                            size_bytes = file_path.stat().st_size
                            size_mb = round(size_bytes / (1024 * 1024), 2)
                            modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
                            
                            total_size_bytes += size_bytes
                            total_size_mb += size_mb
                            source_count += 1
                            source_size += size_mb
                            files_by_type["csv"] += 1
                            
                            if latest_collection_date is None or modified_at > latest_collection_date:
                                latest_collection_date = modified_at
                        except Exception as e:
                            logger.debug(f"Error processing file {file_path}: {e}")
                            continue
                    
                    # Count Parquet files
                    parquet_files = list(source_dir.glob("*.parquet"))
                    for file_path in parquet_files:
                        try:
                            size_bytes = file_path.stat().st_size
                            size_mb = round(size_bytes / (1024 * 1024), 2)
                            modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
                            
                            total_size_bytes += size_bytes
                            total_size_mb += size_mb
                            source_count += 1
                            source_size += size_mb
                            files_by_type["parquet"] += 1
                            
                            if latest_collection_date is None or modified_at > latest_collection_date:
                                latest_collection_date = modified_at
                        except Exception as e:
                            logger.debug(f"Error processing file {file_path}: {e}")
                            continue
                    
                    if source_count > 0:
                        sources_count[src.upper()] = source_count
                        files_by_source[src.upper()] = {
                            "count": source_count,
                            "total_size_mb": round(source_size, 2),
                        }
                except Exception as e:
                    logger.warning(f"Error processing source directory {src}: {e}")
                    continue
        
        # Calculate average file size
        total_files = sum(files_by_type.values())
        avg_file_size_mb = round(total_size_mb / total_files, 2) if total_files > 0 else 0
        
        # Get quality metrics from metadata (skip if timeout/error)
        avg_quality_score = None
        datasets_with_quality = 0
        try:
            manager = MetadataManager()
            all_metadata = manager.get_all_metadata(limit=100) or []  # Limit to 100 to avoid timeout
            quality_scores = [meta.get("quality_score") for meta in all_metadata if meta.get("quality_score") is not None]
            if quality_scores:
                avg_quality_score = round(sum(quality_scores) / len(quality_scores), 2)
                datasets_with_quality = len(quality_scores)
        except Exception as e:
            logger.debug(f"Could not get quality metrics: {e}")
        
        return {
            "summary": {
                "total_datasets": metadata_stats.get("total_datasets", 0),
                "total_files": total_files,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_mb, 2),
                "total_size_gb": round(total_size_mb / 1024, 2),
                "average_file_size_mb": avg_file_size_mb,
                "latest_collection_date": latest_collection_date.isoformat() if latest_collection_date else None,
            },
            "by_source": {
                "counts": sources_count,
                "details": files_by_source,
                "metadata_counts": metadata_stats.get("by_source", {}),
            },
            "by_data_type": {
                "file_types": files_by_type,
                "metadata_types": metadata_stats.get("by_data_type", {}),
            },
            "quality_metrics": {
                "average_quality_score": avg_quality_score,
                "datasets_with_quality": datasets_with_quality,
            },
            "collection_activity": {
                "sources_active": len(sources_count),
                "files_collected": total_files,
                "last_update": latest_collection_date.isoformat() if latest_collection_date else None,
            },
        }
        
    except Exception as e:
        logger.error(f"Error getting aggregated statistics: {e}", exc_info=True)
        return {
            "summary": {
                "total_datasets": 0,
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "total_size_gb": 0,
                "average_file_size_mb": 0,
                "latest_collection_date": None,
            },
            "by_source": {"counts": {}, "details": {}, "metadata_counts": {}},
            "by_data_type": {"file_types": {}, "metadata_types": {}},
            "quality_metrics": {"average_quality_score": None, "datasets_with_quality": 0},
            "collection_activity": {"sources_active": 0, "files_collected": 0, "last_update": None},
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


class ImportDatasetRequest(BaseModel):
    """Request model for importing collected dataset"""
    
    dataset_path: str = Field(..., description="Path to collected dataset file")
    source: Optional[str] = Field(None, description="Data source (tcga, geo, kaggle)")
    map_columns: Optional[Dict[str, str]] = Field(None, description="Column mapping to match patient schema")


@router.post("/import-to-database")
async def import_collected_data(
    request: ImportDatasetRequest,
    db: Session = Depends(get_db),
):
    """Import collected dataset into the database as patients"""
    import pandas as pd
    import logging
    from pathlib import Path
    from datetime import datetime
    from app.models.patient import Patient
    
    logger = logging.getLogger(__name__)
    
    try:
        dataset_path = Path(request.dataset_path)
        
        # Check if file exists
        if not dataset_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Dataset file not found: {request.dataset_path}"
            )
        
        # Load dataset
        if dataset_path.suffix.lower() == '.csv':
            df = pd.read_csv(dataset_path)
        elif dataset_path.suffix.lower() == '.parquet':
            df = pd.read_parquet(dataset_path)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {dataset_path.suffix}"
            )
        
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="Dataset file is empty"
            )
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        
        # Map columns to patient schema if mapping provided
        if request.map_columns:
            df = df.rename(columns=request.map_columns)
        
        # Try to map common column names
        column_mapping = {
            'patient_id': ['patient_id', 'id', 'subject_id', 'case_id'],
            'age': ['age', 'age_at_diagnosis', 'age_at_index'],
            'gender': ['gender', 'sex'],
            'ethnicity': ['ethnicity', 'race', 'race_ethnicity'],
            'has_cancer': ['has_cancer', 'cancer_status', 'diagnosis'],
            'cancer_type': ['cancer_type', 'tumor_type', 'primary_diagnosis'],
            'cancer_subtype': ['cancer_subtype', 'histological_type', 'histology'],
        }
        
        # Apply automatic column mapping
        for target_col, possible_names in column_mapping.items():
            if target_col not in df.columns:
                for name in possible_names:
                    if name in df.columns:
                        df[target_col] = df[name]
                        break
        
        # Ensure required columns exist or create defaults
        if 'patient_id' not in df.columns:
            df['patient_id'] = [f"PAT_{i+1:06d}" for i in range(len(df))]
        
        # Convert has_cancer to boolean if it's a string
        if 'has_cancer' in df.columns:
            if df['has_cancer'].dtype == 'object':
                df['has_cancer'] = df['has_cancer'].astype(str).str.lower().isin(
                    ['true', 'yes', '1', 'cancer', 'positive']
                )
        
        # Import patients
        imported_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            try:
                # Check if patient already exists
                existing = db.query(Patient).filter(
                    Patient.patient_id == str(row.get('patient_id', ''))
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new patient
                patient = Patient(
                    patient_id=str(row.get('patient_id', f"PAT_{imported_count+1:06d}")),
                    age=int(row.get('age', 0)) if pd.notna(row.get('age')) else None,
                    gender=str(row.get('gender', 'Unknown')) if pd.notna(row.get('gender')) else None,
                    ethnicity=str(row.get('ethnicity')) if pd.notna(row.get('ethnicity')) else None,
                    has_cancer=bool(row.get('has_cancer', False)) if pd.notna(row.get('has_cancer')) else False,
                    cancer_type=str(row.get('cancer_type')) if pd.notna(row.get('cancer_type')) else None,
                    cancer_subtype=str(row.get('cancer_subtype')) if pd.notna(row.get('cancer_subtype')) else None,
                )
                
                db.add(patient)
                imported_count += 1
                
            except Exception as e:
                logger.warning(f"Error importing patient row: {e}")
                skipped_count += 1
                continue
        
        db.commit()
        
        return {
            "message": "Dataset imported successfully",
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "total_rows": len(df),
            "dataset_path": request.dataset_path,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing dataset: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error importing dataset: {str(e)}"
        )
