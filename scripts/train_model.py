"""
Script to train ML models from command line
"""
import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.services.ml_training import MLTrainingPipeline
from app.services.model_registry import ModelRegistry


def main():
    parser = argparse.ArgumentParser(description="Train machine learning models")
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to training data CSV",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target column name",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="RandomForest",
        choices=["LogisticRegression", "RandomForest", "XGBoost", "LightGBM", "NeuralNetwork"],
        help="Model type to train",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        help="Train multiple models",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set size (default: 0.2)",
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=0.1,
        help="Validation set size (default: 0.1)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments",
        help="Output directory for experiments",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare all trained models",
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data}...")
    data = pd.read_csv(args.data)
    print(f"Data shape: {data.shape}")

    # Initialize pipeline
    experiment_name = f"{args.model}_{args.target}"
    pipeline = MLTrainingPipeline(experiment_name=experiment_name)

    # Prepare data
    print("\nPreparing data...")
    X_train, y_train, X_val, y_val, X_test, y_test = pipeline.prepare_data(
        data,
        args.target,
        test_size=args.test_size,
        val_size=args.val_size,
    )

    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Train model(s)
    if args.models:
        print(f"\nTraining multiple models: {args.models}")
        results = pipeline.train_all_models(X_train, y_train, X_val, y_val, models=args.models)
    else:
        print(f"\nTraining {args.model}...")
        results = pipeline.train_model(
            args.model, X_train, y_train, X_val, y_val
        )
        results = {args.model: results}

    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_results = {}
    for model_name in results.keys():
        if model_name in pipeline.models:
            metrics = pipeline.evaluate_model(model_name, X_test, y_test)
            test_results[model_name] = metrics
            print(f"\n{model_name} Test Metrics:")
            print(f"  Accuracy: {metrics['accuracy']:.4f}")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall: {metrics['recall']:.4f}")
            print(f"  F1 Score: {metrics['f1_score']:.4f}")
            print(f"  ROC AUC: {metrics.get('roc_auc', 0):.4f}")

    # Compare models if requested
    if args.compare or args.models:
        print("\n" + "=" * 50)
        print("Model Comparison:")
        print("=" * 50)
        comparison = pipeline.compare_models(X_test, y_test)
        print(comparison.to_string(index=False))

    # Save experiment
    print(f"\nSaving experiment to {args.output_dir}/...")
    pipeline.save_experiment(output_dir=args.output_dir)

    # Register models
    registry = ModelRegistry()
    for model_name, model in pipeline.models.items():
        model_path = f"{args.output_dir}/{experiment_name}_{model_name}.pkl"
        model_id = registry.register_model(
            model_name=model_name,
            model_type=model_name,
            model_path=model_path,
            metrics=test_results.get(model_name, {}),
            feature_names=model.feature_names,
        )
        print(f"  ✅ {model_name} registered with ID: {model_id}")

    print("\n✅ Training complete!")


if __name__ == "__main__":
    main()

