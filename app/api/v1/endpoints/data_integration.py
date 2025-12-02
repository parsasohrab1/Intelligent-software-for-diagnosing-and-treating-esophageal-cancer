"""
Data integration endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
import pandas as pd

from app.core.database import get_db
from app.services.data_integration.hybrid_integrator import HybridDataIntegrator
from app.services.feature_engineering import FeatureEngineer
from app.services.data_augmentation import DataAugmenter
from app.services.data_warehouse import DataWarehouse

router = APIRouter()


class IntegrateDataRequest(BaseModel):
    """Request model for data integration"""

    synthetic_data_path: Optional[str] = Field(None, description="Path to synthetic data")
    real_data_path: Optional[str] = Field(None, description="Path to real data")
    fusion_method: str = Field(
        default="concatenate",
        description="Fusion method: concatenate, weighted, or matched",
    )
    matching_threshold: float = Field(
        default=0.8, description="Threshold for matching method"
    )


class FeatureEngineeringRequest(BaseModel):
    """Request model for feature engineering"""

    data_path: str = Field(..., description="Path to data file")
    include_genomic: bool = Field(default=True, description="Include genomic features")
    include_lab: bool = Field(default=True, description="Include lab features")
    normalize: bool = Field(default=True, description="Normalize features")
    normalization_method: str = Field(
        default="standard", description="Normalization method: standard or minmax"
    )


class AugmentDataRequest(BaseModel):
    """Request model for data augmentation"""

    real_data_path: str = Field(..., description="Path to real data")
    synthetic_data_path: str = Field(..., description="Path to synthetic data")
    target_column: str = Field(..., description="Target column name")
    augmentation_ratio: float = Field(
        default=0.5, description="Ratio of synthetic to real data"
    )
    method: str = Field(
        default="synthetic",
        description="Augmentation method: synthetic, smote, adasyn, or combined",
    )


@router.post("/integrate")
async def integrate_data(request: IntegrateDataRequest):
    """Integrate synthetic and real data"""
    try:
        integrator = HybridDataIntegrator()

        # Load data
        if request.synthetic_data_path:
            synthetic_data = pd.read_csv(request.synthetic_data_path)
        else:
            raise HTTPException(status_code=400, detail="Synthetic data path required")

        if request.real_data_path:
            real_data = pd.read_csv(request.real_data_path)
        else:
            raise HTTPException(status_code=400, detail="Real data path required")

        # Statistical matching
        key_columns = ["age", "gender", "has_cancer"] if "has_cancer" in synthetic_data.columns else ["age", "gender"]
        matching_scores = integrator.statistical_matching(
            synthetic_data, real_data, key_columns
        )

        # Fuse datasets
        fused_data = integrator.fuse_datasets(
            synthetic_data,
            real_data,
            fusion_method=request.fusion_method,
            matching_threshold=request.matching_threshold,
        )

        # Calculate quality metrics
        quality_metrics = integrator.calculate_quality_metrics(fused_data)

        # Detect bias
        sensitive_columns = ["gender", "ethnicity"] if "ethnicity" in fused_data.columns else ["gender"]
        bias_report = integrator.detect_bias(fused_data, sensitive_columns)

        return {
            "message": "Data integration completed",
            "matching_scores": matching_scores,
            "quality_metrics": quality_metrics,
            "bias_report": bias_report,
            "fused_data_size": len(fused_data),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error integrating data: {str(e)}")


@router.post("/engineer-features")
async def engineer_features(request: FeatureEngineeringRequest):
    """Engineer features from multi-modal data"""
    try:
        engineer = FeatureEngineer()

        # Load data
        data = pd.read_csv(request.data_path)

        # Extract features from different sources
        if "patient_id" in data.columns or "age" in data.columns:
            patient_features = engineer.extract_features_from_patients(data)
        else:
            patient_features = pd.DataFrame()

        if "bmi" in data.columns or "t_stage" in data.columns:
            clinical_features = engineer.extract_features_from_clinical(data)
        else:
            clinical_features = pd.DataFrame()

        genomic_features = None
        if request.include_genomic and "mutations" in data.columns:
            genomic_features = engineer.extract_features_from_genomic(data)

        lab_features = None
        if request.include_lab and "test_type" in data.columns:
            lab_features = engineer.extract_features_from_lab(data)

        # Combine features
        combined_features = engineer.combine_features(
            patient_features,
            clinical_features,
            genomic_features,
            lab_features,
        )

        # Normalize if requested
        if request.normalize:
            combined_features = engineer.normalize_features(
                combined_features, method=request.normalization_method
            )

        return {
            "message": "Feature engineering completed",
            "feature_count": len(combined_features.columns),
            "sample_count": len(combined_features),
            "features": combined_features.columns.tolist(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error engineering features: {str(e)}"
        )


@router.post("/augment")
async def augment_data(request: AugmentDataRequest):
    """Augment real data with synthetic samples"""
    try:
        augmenter = DataAugmenter(method=request.method)

        # Load data
        real_data = pd.read_csv(request.real_data_path)
        synthetic_data = pd.read_csv(request.synthetic_data_path)

        # Augment
        if request.method == "synthetic":
            augmented_data = augmenter.augment_with_synthetic(
                real_data,
                synthetic_data,
                request.target_column,
                request.augmentation_ratio,
            )
        else:
            # For SMOTE/ADASYN, need to separate X and y
            X = real_data.drop(columns=[request.target_column])
            y = real_data[request.target_column]

            if request.method == "smote":
                X_aug, y_aug = augmenter.augment_with_smote(X, y)
            elif request.method == "adasyn":
                X_aug, y_aug = augmenter.augment_with_adasyn(X, y)
            elif request.method == "combined":
                X_aug, y_aug = augmenter.augment_with_combined(X, y)
            else:
                raise ValueError(f"Unknown augmentation method: {request.method}")

            augmented_data = pd.concat([X_aug, y_aug], axis=1)

        # Validate augmentation
        validation = augmenter.validate_augmentation(
            real_data, augmented_data, request.target_column
        )

        return {
            "message": "Data augmentation completed",
            "validation": validation,
            "augmented_size": len(augmented_data),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error augmenting data: {str(e)}"
        )


@router.post("/warehouse/load")
async def load_to_warehouse(
    data_type: str,
    data_path: str,
    db: Session = Depends(get_db),
):
    """Load data to warehouse"""
    try:
        warehouse = DataWarehouse()
        warehouse.create_schema()

        data = pd.read_csv(data_path)

        if data_type == "patients":
            warehouse.load_fact_patients(data)
        elif data_type == "clinical":
            warehouse.load_fact_clinical_events(data)
        elif data_type == "features":
            warehouse.load_features(data)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

        return {"message": f"Data loaded to warehouse: {data_type}"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading to warehouse: {str(e)}"
        )


@router.get("/warehouse/query")
async def query_warehouse(query: str):
    """Query data warehouse"""
    try:
        warehouse = DataWarehouse()
        result = warehouse.query_warehouse(query)
        return {"data": result.to_dict(orient="records"), "count": len(result)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying warehouse: {str(e)}"
        )


@router.get("/warehouse/statistics")
async def get_warehouse_statistics():
    """Get warehouse statistics"""
    try:
        warehouse = DataWarehouse()
        stats = warehouse.get_feature_statistics()
        return {"statistics": stats.to_dict(orient="records")}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting statistics: {str(e)}"
        )

