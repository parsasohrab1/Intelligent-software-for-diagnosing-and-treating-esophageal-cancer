"""
Strategic Database Indexing Module

This module provides:
- Strategic index definitions for all tables
- Partial indexes for optimized query patterns
- Composite indexes for common query combinations
- Index management and monitoring utilities
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy import text, Index
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.database import engine, SessionLocal

logger = logging.getLogger(__name__)


# ============================================================================
# Strategic Index Definitions
# ============================================================================

# Patient Table Indexes
PATIENT_INDEXES = [
    # Primary lookup by patient_id (already exists as primary key)
    
    # Filtering by cancer status - very common query
    {
        "name": "ix_patients_has_cancer",
        "table": "patients",
        "columns": ["has_cancer"],
        "comment": "Filter patients by cancer status"
    },
    
    # Date-based queries for time series analysis
    {
        "name": "ix_patients_created_at",
        "table": "patients",
        "columns": ["created_at"],
        "comment": "Sort/filter patients by creation date"
    },
    
    # Composite: Cancer patients by type
    {
        "name": "ix_patients_cancer_type_subtype",
        "table": "patients",
        "columns": ["cancer_type", "cancer_subtype"],
        "where": "has_cancer = true",
        "comment": "Partial index for cancer patients by type"
    },
    
    # Demographics filtering
    {
        "name": "ix_patients_age_gender",
        "table": "patients",
        "columns": ["age", "gender"],
        "comment": "Filter by demographics"
    },
    
    # Ethnicity studies
    {
        "name": "ix_patients_ethnicity",
        "table": "patients",
        "columns": ["ethnicity"],
        "comment": "Filter by ethnicity for population studies"
    },
]

# Imaging Data Indexes
IMAGING_DATA_INDEXES = [
    # Patient lookup - very frequent
    {
        "name": "ix_imaging_patient_id",
        "table": "imaging_data",
        "columns": ["patient_id"],
        "comment": "Lookup imaging by patient"
    },
    
    # Filter by modality (MRI, CT, etc.)
    {
        "name": "ix_imaging_modality",
        "table": "imaging_data",
        "columns": ["imaging_modality"],
        "comment": "Filter by imaging modality"
    },
    
    # Composite: Patient + Modality (common query pattern)
    {
        "name": "ix_imaging_patient_modality",
        "table": "imaging_data",
        "columns": ["patient_id", "imaging_modality"],
        "comment": "Patient images by modality"
    },
    
    # Date-based queries
    {
        "name": "ix_imaging_date",
        "table": "imaging_data",
        "columns": ["imaging_date"],
        "comment": "Sort/filter by imaging date"
    },
    
    # MRI-specific index (partial)
    {
        "name": "ix_imaging_mri_tumor",
        "table": "imaging_data",
        "columns": ["tumor_length_cm", "wall_thickness_cm"],
        "where": "imaging_modality = 'MRI'",
        "comment": "MRI tumor measurements (partial index)"
    },
    
    # Radiologist workload queries
    {
        "name": "ix_imaging_radiologist",
        "table": "imaging_data",
        "columns": ["radiologist_id", "imaging_date"],
        "comment": "Radiologist workload analysis"
    },
]

# Clinical Data Indexes
CLINICAL_DATA_INDEXES = [
    # Patient lookup
    {
        "name": "ix_clinical_patient_id",
        "table": "clinical_data",
        "columns": ["patient_id"],
        "comment": "Lookup clinical data by patient"
    },
    
    # Cancer staging (TNM) - very important for CDS queries
    {
        "name": "ix_clinical_tnm_staging",
        "table": "clinical_data",
        "columns": ["t_stage", "n_stage", "m_stage"],
        "comment": "TNM staging queries"
    },
    
    # Tumor location analysis
    {
        "name": "ix_clinical_tumor_location",
        "table": "clinical_data",
        "columns": ["tumor_location"],
        "comment": "Filter by tumor location"
    },
    
    # Examination date for time series
    {
        "name": "ix_clinical_exam_date",
        "table": "clinical_data",
        "columns": ["examination_date"],
        "comment": "Sort by examination date"
    },
    
    # Histological analysis
    {
        "name": "ix_clinical_histological",
        "table": "clinical_data",
        "columns": ["histological_grade"],
        "comment": "Histological grade analysis"
    },
    
    # Advanced cases (invasion positive)
    {
        "name": "ix_clinical_invasion",
        "table": "clinical_data",
        "columns": ["lymphovascular_invasion", "perineural_invasion"],
        "where": "lymphovascular_invasion = true OR perineural_invasion = true",
        "comment": "Partial index for invasion cases"
    },
]

# Treatment Data Indexes
TREATMENT_DATA_INDEXES = [
    # Patient lookup
    {
        "name": "ix_treatment_patient_id",
        "table": "treatment_data",
        "columns": ["patient_id"],
        "comment": "Lookup treatment by patient"
    },
    
    # Response analysis
    {
        "name": "ix_treatment_response",
        "table": "treatment_data",
        "columns": ["best_response"],
        "comment": "Treatment response analysis"
    },
    
    # Survival analysis
    {
        "name": "ix_treatment_survival",
        "table": "treatment_data",
        "columns": ["vital_status", "survival_days"],
        "comment": "Survival analysis queries"
    },
    
    # Timeline queries
    {
        "name": "ix_treatment_dates",
        "table": "treatment_data",
        "columns": ["diagnosis_date", "response_date"],
        "comment": "Treatment timeline analysis"
    },
    
    # Complications tracking
    {
        "name": "ix_treatment_complications",
        "table": "treatment_data",
        "columns": ["treatment_complications"],
        "where": "treatment_complications = true",
        "comment": "Partial index for complication cases"
    },
]

# Genomic Data Indexes
GENOMIC_DATA_INDEXES = [
    # Patient lookup
    {
        "name": "ix_genomic_patient_id",
        "table": "genomic_data",
        "columns": ["patient_id"],
        "comment": "Lookup genomic data by patient"
    },
    
    # Biomarker queries (PD-L1, MSI)
    {
        "name": "ix_genomic_pdl1",
        "table": "genomic_data",
        "columns": ["pdl1_status", "pdl1_percentage"],
        "comment": "PD-L1 biomarker queries"
    },
    
    {
        "name": "ix_genomic_msi",
        "table": "genomic_data",
        "columns": ["msi_status"],
        "comment": "MSI status queries"
    },
    
    # Sequencing platform
    {
        "name": "ix_genomic_platform",
        "table": "genomic_data",
        "columns": ["sequencing_platform"],
        "comment": "Platform-specific queries"
    },
    
    # Date-based
    {
        "name": "ix_genomic_seq_date",
        "table": "genomic_data",
        "columns": ["sequencing_date"],
        "comment": "Sort by sequencing date"
    },
]

# All indexes combined
ALL_INDEXES = (
    PATIENT_INDEXES +
    IMAGING_DATA_INDEXES +
    CLINICAL_DATA_INDEXES +
    TREATMENT_DATA_INDEXES +
    GENOMIC_DATA_INDEXES
)


# ============================================================================
# Index Management Functions
# ============================================================================

def get_database_type() -> str:
    """Detect database type (postgresql or sqlite)"""
    from app.core.config import settings
    if settings.USE_SQLITE:
        return "sqlite"
    return "postgresql"


def create_index_sql(index_def: Dict, db_type: str) -> str:
    """Generate CREATE INDEX SQL statement"""
    name = index_def["name"]
    table = index_def["table"]
    columns = ", ".join(index_def["columns"])
    where_clause = index_def.get("where", "")
    
    if db_type == "postgresql" and where_clause:
        # PostgreSQL supports partial indexes
        return f"""
            CREATE INDEX IF NOT EXISTS {name}
            ON {table} ({columns})
            WHERE {where_clause}
        """
    elif db_type == "sqlite":
        # SQLite partial indexes (since 3.8.0)
        if where_clause:
            return f"""
                CREATE INDEX IF NOT EXISTS {name}
                ON {table} ({columns})
                WHERE {where_clause}
            """
        return f"""
            CREATE INDEX IF NOT EXISTS {name}
            ON {table} ({columns})
        """
    else:
        # Standard index without partial support
        return f"""
            CREATE INDEX IF NOT EXISTS {name}
            ON {table} ({columns})
        """


def drop_index_sql(index_name: str, table_name: str, db_type: str) -> str:
    """Generate DROP INDEX SQL statement"""
    if db_type == "postgresql":
        return f"DROP INDEX IF EXISTS {index_name}"
    else:
        return f"DROP INDEX IF EXISTS {index_name}"


def create_all_indexes(session: Optional[Session] = None) -> Dict[str, bool]:
    """
    Create all strategic indexes.
    Returns dict of index_name -> success status.
    """
    db_type = get_database_type()
    results = {}
    
    if session is None:
        session = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        for index_def in ALL_INDEXES:
            name = index_def["name"]
            try:
                sql = create_index_sql(index_def, db_type)
                session.execute(text(sql))
                session.commit()
                results[name] = True
                logger.info(f"Created index: {name}")
            except (OperationalError, ProgrammingError) as e:
                session.rollback()
                if "already exists" in str(e).lower():
                    results[name] = True
                    logger.debug(f"Index already exists: {name}")
                else:
                    results[name] = False
                    logger.warning(f"Failed to create index {name}: {e}")
            except Exception as e:
                session.rollback()
                results[name] = False
                logger.error(f"Error creating index {name}: {e}")
    finally:
        if should_close:
            session.close()
    
    return results


def drop_all_indexes(session: Optional[Session] = None) -> Dict[str, bool]:
    """Drop all strategic indexes"""
    db_type = get_database_type()
    results = {}
    
    if session is None:
        session = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        for index_def in ALL_INDEXES:
            name = index_def["name"]
            table = index_def["table"]
            try:
                sql = drop_index_sql(name, table, db_type)
                session.execute(text(sql))
                session.commit()
                results[name] = True
                logger.info(f"Dropped index: {name}")
            except Exception as e:
                session.rollback()
                results[name] = False
                logger.warning(f"Failed to drop index {name}: {e}")
    finally:
        if should_close:
            session.close()
    
    return results


def get_existing_indexes(session: Optional[Session] = None) -> Dict[str, List[str]]:
    """Get existing indexes per table"""
    db_type = get_database_type()
    
    if session is None:
        session = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        if db_type == "postgresql":
            result = session.execute(text("""
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """))
        else:  # SQLite
            result = session.execute(text("""
                SELECT tbl_name, name
                FROM sqlite_master
                WHERE type = 'index'
                ORDER BY tbl_name, name
            """))
        
        indexes = {}
        for row in result:
            table = row[0]
            index = row[1]
            if table not in indexes:
                indexes[table] = []
            indexes[table].append(index)
        
        return indexes
    finally:
        if should_close:
            session.close()


def analyze_index_usage(session: Optional[Session] = None) -> Dict:
    """
    Analyze index usage statistics (PostgreSQL only).
    Returns usage stats for optimization recommendations.
    """
    db_type = get_database_type()
    
    if db_type != "postgresql":
        return {"error": "Index usage analysis only available for PostgreSQL"}
    
    if session is None:
        session = SessionLocal()
        should_close = True
    else:
        should_close = False
    
    try:
        # Get index usage stats
        result = session.execute(text("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan as index_scans,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
        """))
        
        stats = []
        for row in result:
            stats.append({
                "schema": row[0],
                "table": row[1],
                "index": row[2],
                "scans": row[3],
                "tuples_read": row[4],
                "tuples_fetched": row[5],
                "size": row[6]
            })
        
        # Identify unused indexes
        unused = [s for s in stats if s["scans"] == 0]
        
        # Identify heavily used indexes
        heavy_usage = [s for s in stats if s["scans"] > 1000]
        
        return {
            "all_indexes": stats,
            "unused_indexes": unused,
            "heavy_usage_indexes": heavy_usage,
            "total_indexes": len(stats),
            "recommendations": generate_index_recommendations(stats)
        }
    finally:
        if should_close:
            session.close()


def generate_index_recommendations(stats: List[Dict]) -> List[str]:
    """Generate recommendations based on index usage"""
    recommendations = []
    
    # Check for unused indexes
    unused = [s for s in stats if s["scans"] == 0]
    if unused:
        recommendations.append(
            f"Consider dropping {len(unused)} unused indexes: " +
            ", ".join(s["index"] for s in unused[:5])
        )
    
    # Check for indexes with low tuple fetch ratio
    for stat in stats:
        if stat["tuples_read"] > 0 and stat["tuples_fetched"] > 0:
            ratio = stat["tuples_fetched"] / stat["tuples_read"]
            if ratio < 0.1 and stat["scans"] > 100:
                recommendations.append(
                    f"Index {stat['index']} has low selectivity ({ratio:.2%}). "
                    "Consider reviewing query patterns."
                )
    
    return recommendations


def get_index_health_report() -> Dict:
    """Generate comprehensive index health report"""
    session = SessionLocal()
    try:
        db_type = get_database_type()
        existing = get_existing_indexes(session)
        
        # Check which strategic indexes exist
        strategic_status = {}
        for index_def in ALL_INDEXES:
            name = index_def["name"]
            table = index_def["table"]
            exists = name in existing.get(table, [])
            strategic_status[name] = {
                "exists": exists,
                "table": table,
                "columns": index_def["columns"],
                "is_partial": "where" in index_def
            }
        
        # Calculate coverage
        total = len(ALL_INDEXES)
        existing_count = sum(1 for s in strategic_status.values() if s["exists"])
        
        report = {
            "database_type": db_type,
            "strategic_indexes": strategic_status,
            "coverage": {
                "total_defined": total,
                "existing": existing_count,
                "missing": total - existing_count,
                "percentage": round((existing_count / total) * 100, 2) if total > 0 else 0
            },
            "all_existing_indexes": existing,
        }
        
        # Add usage stats for PostgreSQL
        if db_type == "postgresql":
            report["usage_analysis"] = analyze_index_usage(session)
        
        return report
    finally:
        session.close()


# ============================================================================
# Initialization Function (called on app startup)
# ============================================================================

async def initialize_indexes():
    """Initialize all strategic indexes on application startup"""
    logger.info("Initializing strategic database indexes...")
    
    try:
        results = create_all_indexes()
        
        success_count = sum(1 for v in results.values() if v)
        total = len(results)
        
        logger.info(f"Index initialization complete: {success_count}/{total} indexes ready")
        
        if success_count < total:
            failed = [k for k, v in results.items() if not v]
            logger.warning(f"Failed indexes: {failed}")
        
        return results
    except Exception as e:
        logger.error(f"Index initialization failed: {e}")
        return {}
