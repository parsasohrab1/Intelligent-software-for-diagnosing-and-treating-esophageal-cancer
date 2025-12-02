"""
Data warehouse for integrated data
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import create_engine, text
from app.core.config import settings


class DataWarehouse:
    """Data warehouse for storing integrated and processed data"""

    def __init__(self):
        # Use separate database for warehouse
        warehouse_url = settings.DATABASE_URL.replace(
            settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_warehouse"
        )
        self.engine = create_engine(warehouse_url, pool_pre_ping=True)

    def create_schema(self):
        """Create data warehouse schema"""
        with self.engine.connect() as conn:
            # Fact table for patient data
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS fact_patients (
                    patient_id VARCHAR(50) PRIMARY KEY,
                    age INTEGER,
                    gender VARCHAR(10),
                    has_cancer BOOLEAN,
                    cancer_type VARCHAR(50),
                    data_source VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )

            # Fact table for clinical events
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS fact_clinical_events (
                    event_id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50),
                    event_date DATE,
                    event_type VARCHAR(50),
                    t_stage VARCHAR(10),
                    n_stage VARCHAR(10),
                    m_stage VARCHAR(10),
                    tumor_size FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )

            # Dimension table for features
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS dim_features (
                    feature_id SERIAL PRIMARY KEY,
                    feature_name VARCHAR(100) UNIQUE,
                    feature_type VARCHAR(50),
                    feature_category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
            )

            # Fact table for features
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS fact_features (
                    patient_id VARCHAR(50),
                    feature_id INTEGER,
                    feature_value FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (patient_id, feature_id),
                    FOREIGN KEY (feature_id) REFERENCES dim_features(feature_id)
                )
                """)
            )

            conn.commit()

    def load_fact_patients(self, patients_df: pd.DataFrame):
        """Load patient fact table"""
        patients_df.to_sql(
            "fact_patients",
            self.engine,
            if_exists="append",
            index=False,
            method="multi",
        )

    def load_fact_clinical_events(self, clinical_df: pd.DataFrame):
        """Load clinical events fact table"""
        clinical_df.to_sql(
            "fact_clinical_events",
            self.engine,
            if_exists="append",
            index=False,
            method="multi",
        )

    def load_features(
        self, features_df: pd.DataFrame, feature_metadata: Optional[Dict] = None
    ):
        """Load features to warehouse"""
        # Load feature dimensions
        if feature_metadata:
            feature_dim_df = pd.DataFrame(
                [
                    {
                        "feature_name": name,
                        "feature_type": meta.get("type", "numeric"),
                        "feature_category": meta.get("category", "unknown"),
                    }
                    for name, meta in feature_metadata.items()
                ]
            )
            feature_dim_df.to_sql(
                "dim_features",
                self.engine,
                if_exists="append",
                index=False,
            )

        # Load feature facts (melt features)
        feature_facts = features_df.melt(
            id_vars=["patient_id"] if "patient_id" in features_df.columns else [],
            var_name="feature_name",
            value_name="feature_value",
        )

        # Get feature IDs
        with self.engine.connect() as conn:
            feature_ids = pd.read_sql(
                "SELECT feature_id, feature_name FROM dim_features", conn
            )
            feature_facts = feature_facts.merge(
                feature_ids, on="feature_name", how="left"
            )
            feature_facts = feature_facts.dropna(subset=["feature_id"])

        feature_facts[["patient_id", "feature_id", "feature_value"]].to_sql(
            "fact_features",
            self.engine,
            if_exists="append",
            index=False,
        )

    def query_warehouse(self, query: str) -> pd.DataFrame:
        """Query data warehouse"""
        return pd.read_sql(query, self.engine)

    def get_patient_features(self, patient_id: str) -> pd.DataFrame:
        """Get all features for a patient"""
        query = """
        SELECT f.feature_name, ff.feature_value
        FROM fact_features ff
        JOIN dim_features f ON ff.feature_id = f.feature_id
        WHERE ff.patient_id = :patient_id
        """
        return pd.read_sql(query, self.engine, params={"patient_id": patient_id})

    def get_feature_statistics(self) -> pd.DataFrame:
        """Get statistics for all features"""
        query = """
        SELECT 
            f.feature_name,
            f.feature_type,
            f.feature_category,
            COUNT(ff.feature_value) as count,
            AVG(ff.feature_value) as mean,
            STDDEV(ff.feature_value) as stddev,
            MIN(ff.feature_value) as min_val,
            MAX(ff.feature_value) as max_val
        FROM dim_features f
        LEFT JOIN fact_features ff ON f.feature_id = ff.feature_id
        GROUP BY f.feature_id, f.feature_name, f.feature_type, f.feature_category
        """
        return pd.read_sql(query, self.engine)

