"""
Data quality assessment module
"""
import pandas as pd
from typing import Dict, List
import numpy as np


class DataQualityAssessor:
    """Assess data quality metrics"""

    def assess_quality(self, data: pd.DataFrame) -> Dict:
        """Comprehensive data quality assessment"""
        quality_report = {
            "completeness": self.assess_completeness(data),
            "consistency": self.assess_consistency(data),
            "accuracy": self.assess_accuracy(data),
            "timeliness": self.assess_timeliness(data),
            "relevance": self.assess_relevance(data),
            "overall_score": 0.0,
        }

        # Calculate overall score
        scores = [
            quality_report["completeness"]["score"],
            quality_report["consistency"]["score"],
            quality_report["accuracy"]["score"],
            quality_report["timeliness"]["score"],
            quality_report["relevance"]["score"],
        ]
        quality_report["overall_score"] = np.mean(scores)

        return quality_report

    def assess_completeness(self, data: pd.DataFrame) -> Dict:
        """Assess data completeness"""
        total_cells = data.size
        missing_cells = data.isnull().sum().sum()
        completeness_percentage = ((total_cells - missing_cells) / total_cells) * 100

        # Score: 100 if > 95% complete, linear decrease below
        score = max(0, min(100, (completeness_percentage - 50) * 2))

        return {
            "score": score,
            "completeness_percentage": round(completeness_percentage, 2),
            "missing_cells": int(missing_cells),
            "total_cells": int(total_cells),
            "columns_with_missing": data.isnull().any().sum(),
        }

    def assess_consistency(self, data: pd.DataFrame) -> Dict:
        """Assess data consistency"""
        issues = []

        # Check for duplicate rows
        duplicates = data.duplicated().sum()
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate rows found")

        # Check for contradictory values (if applicable)
        # This would be domain-specific

        # Score based on issues found
        score = 100 if len(issues) == 0 else max(0, 100 - len(issues) * 20)

        return {
            "score": score,
            "issues": issues,
            "duplicate_rows": int(duplicates),
        }

    def assess_accuracy(self, data: pd.DataFrame) -> Dict:
        """Assess data accuracy (basic checks)"""
        issues = []

        # Check for out-of-range values in numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if data[col].min() < -1e10 or data[col].max() > 1e10:
                issues.append(f"Column {col} has extreme values")

        # Score based on issues
        score = 100 if len(issues) == 0 else max(0, 100 - len(issues) * 10)

        return {
            "score": score,
            "issues": issues,
        }

    def assess_timeliness(self, data: pd.DataFrame) -> Dict:
        """Assess data timeliness"""
        # Check for date columns
        date_cols = []
        for col in data.columns:
            if "date" in col.lower() or "time" in col.lower():
                date_cols.append(col)

        if not date_cols:
            return {"score": 50, "message": "No date columns found"}

        # For now, assume data is timely if it exists
        return {"score": 100, "date_columns": date_cols}

    def assess_relevance(self, data: pd.DataFrame) -> Dict:
        """Assess data relevance"""
        # Check for relevant columns for esophageal cancer research
        relevant_keywords = [
            "patient",
            "cancer",
            "tumor",
            "stage",
            "treatment",
            "survival",
            "mutation",
            "gene",
        ]

        relevant_columns = []
        for col in data.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in relevant_keywords):
                relevant_columns.append(col)

        relevance_percentage = (len(relevant_columns) / len(data.columns)) * 100 if len(data.columns) > 0 else 0
        score = min(100, relevance_percentage * 2)  # Scale to 100

        return {
            "score": score,
            "relevance_percentage": round(relevance_percentage, 2),
            "relevant_columns": relevant_columns,
            "total_columns": len(data.columns),
        }

