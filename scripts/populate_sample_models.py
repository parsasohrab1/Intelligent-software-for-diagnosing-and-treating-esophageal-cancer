"""
Script to populate sample ML models for frontend display
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.model_registry import ModelRegistry
from app.core.mongodb import get_mongodb_database


def populate_sample_models():
    """Populate sample ML models in the registry"""
    print("=" * 60)
    print("Populating Sample ML Models")
    print("=" * 60)
    
    # Check MongoDB connection
    db = get_mongodb_database()
    if db is None:
        print("ERROR: MongoDB is not available. Please ensure MongoDB is running.")
        print("MongoDB connection is required to store model registry data.")
        return False
    
    registry = ModelRegistry()
    
    # Check if models already exist
    try:
        existing_models = registry.list_models(limit=10)
        if existing_models:
            print(f"Found {len(existing_models)} existing models in registry.")
            response = input("Do you want to add sample models anyway? (y/n): ")
            if response.lower() != 'y':
                print("Skipping population.")
                return True
    except Exception as e:
        print(f"Warning: Could not check existing models: {e}")
        print("Continuing with population...")
    
    # Sample models data
    sample_models = [
        {
            "model_name": "Esophageal Cancer Risk Predictor",
            "model_type": "RandomForest",
            "model_path": "models/sample_randomforest_risk.pkl",
            "metrics": {
                "accuracy": 0.87,
                "precision": 0.85,
                "recall": 0.82,
                "f1_score": 0.83,
                "roc_auc": 0.91,
                "confusion_matrix": [[450, 35], [42, 473]]
            },
            "feature_names": [
                "age", "gender", "bmi", "smoking", "alcohol", 
                "gerd", "barretts_esophagus", "family_history",
                "tumor_length_cm", "t_stage", "n_stage", "m_stage"
            ],
            "training_config": {
                "n_estimators": 100,
                "max_depth": 15,
                "min_samples_split": 5,
                "random_state": 42
            },
            "baseline_statistics": {
                "age": {"mean": 62.5, "std": 12.3, "min": 35, "max": 89},
                "bmi": {"mean": 28.2, "std": 5.1, "min": 18.5, "max": 42.0}
            }
        },
        {
            "model_name": "Treatment Response Predictor",
            "model_type": "XGBoost",
            "model_path": "models/sample_xgboost_treatment.pkl",
            "metrics": {
                "accuracy": 0.79,
                "precision": 0.76,
                "recall": 0.81,
                "f1_score": 0.78,
                "roc_auc": 0.88
            },
            "feature_names": [
                "age", "t_stage", "n_stage", "m_stage", "histological_grade",
                "pdl1_status", "pdl1_percentage", "msi_status", "tumor_length_cm"
            ],
            "training_config": {
                "n_estimators": 150,
                "max_depth": 8,
                "learning_rate": 0.1,
                "subsample": 0.8
            },
            "baseline_statistics": {
                "age": {"mean": 64.2, "std": 11.8, "min": 40, "max": 85},
                "tumor_length_cm": {"mean": 4.2, "std": 2.1, "min": 0.5, "max": 12.0}
            }
        },
        {
            "model_name": "Prognostic Score Calculator",
            "model_type": "LogisticRegression",
            "model_path": "models/sample_logistic_prognostic.pkl",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.80,
                "recall": 0.78,
                "f1_score": 0.79,
                "roc_auc": 0.86
            },
            "feature_names": [
                "age", "gender", "bmi", "ecog_status", "t_stage",
                "n_stage", "m_stage", "tumor_location", "lymph_nodes_positive"
            ],
            "training_config": {
                "C": 1.0,
                "penalty": "l2",
                "solver": "liblinear",
                "max_iter": 1000
            },
            "baseline_statistics": {
                "bmi": {"mean": 27.8, "std": 4.9, "min": 19.0, "max": 38.5},
                "ecog_status": {"mean": 1.2, "std": 0.8, "min": 0, "max": 3}
            }
        },
        {
            "model_name": "Advanced Risk Assessment",
            "model_type": "LightGBM",
            "model_path": "models/sample_lightgbm_advanced.pkl",
            "metrics": {
                "accuracy": 0.91,
                "precision": 0.89,
                "recall": 0.88,
                "f1_score": 0.88,
                "roc_auc": 0.94
            },
            "feature_names": [
                "age", "gender", "bmi", "smoking", "alcohol", "gerd",
                "barretts_esophagus", "family_history", "tumor_length_cm",
                "t_stage", "n_stage", "m_stage", "histological_grade",
                "pdl1_status", "lymph_nodes_positive"
            ],
            "training_config": {
                "n_estimators": 200,
                "max_depth": 12,
                "learning_rate": 0.05,
                "num_leaves": 31
            },
            "baseline_statistics": {
                "age": {"mean": 63.1, "std": 12.5, "min": 38, "max": 87},
                "bmi": {"mean": 28.5, "std": 5.3, "min": 18.0, "max": 40.0}
            }
        },
        {
            "model_name": "Neural Network Classifier",
            "model_type": "NeuralNetwork",
            "model_path": "models/sample_neural_network.pkl",
            "metrics": {
                "accuracy": 0.84,
                "precision": 0.82,
                "recall": 0.83,
                "f1_score": 0.82,
                "roc_auc": 0.89
            },
            "feature_names": [
                "age", "gender", "bmi", "smoking", "alcohol", "gerd",
                "barretts_esophagus", "family_history", "t_stage", "n_stage", "m_stage"
            ],
            "training_config": {
                "hidden_layers": [64, 32, 16],
                "activation": "relu",
                "learning_rate": 0.001,
                "epochs": 100,
                "batch_size": 32
            },
            "baseline_statistics": {
                "age": {"mean": 61.8, "std": 13.2, "min": 36, "max": 88},
                "bmi": {"mean": 27.9, "std": 5.0, "min": 18.5, "max": 39.5}
            }
        }
    ]
    
    print(f"\nRegistering {len(sample_models)} sample models...")
    
    registered_count = 0
    for i, model_data in enumerate(sample_models, 1):
        try:
            # Create model directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            
            # Register model
            model_id = registry.register_model(
                model_name=model_data["model_name"],
                model_type=model_data["model_type"],
                model_path=model_data["model_path"],
                metrics=model_data["metrics"],
                feature_names=model_data["feature_names"],
                training_config=model_data["training_config"],
                baseline_statistics=model_data["baseline_statistics"]
            )
            
            print(f"  [{i}/{len(sample_models)}] [OK] Registered: {model_data['model_name']} (ID: {model_id})")
            registered_count += 1
            
        except Exception as e:
            print(f"  [{i}/{len(sample_models)}] [ERROR] Error registering {model_data['model_name']}: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"Successfully registered {registered_count}/{len(sample_models)} models")
    print(f"{'=' * 60}")
    
    # Verify models
    try:
        print("\nVerifying registered models...")
        all_models = registry.list_models(limit=100)
        print(f"Total models in registry: {len(all_models)}")
        
        if all_models:
            print("\nRegistered Models:")
            for model in all_models:
                print(f"  - {model.get('model_name', 'Unknown')} ({model.get('model_type', 'Unknown')})")
                print(f"    ID: {model.get('model_id', 'N/A')}")
                print(f"    Accuracy: {model.get('metrics', {}).get('accuracy', 0):.2%}")
                print(f"    Status: {model.get('status', 'unknown')}")
                print()
    except Exception as e:
        print(f"Warning: Could not verify models: {e}")
    
    return registered_count > 0


if __name__ == "__main__":
    try:
        success = populate_sample_models()
        if success:
            print("\n[SUCCESS] Sample models populated successfully!")
            print("You can now view them in the ML Models page in the frontend.")
        else:
            print("\n[FAILED] Failed to populate sample models.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
