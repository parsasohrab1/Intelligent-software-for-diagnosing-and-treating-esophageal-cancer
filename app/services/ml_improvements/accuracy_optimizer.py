"""
Accuracy Optimization Module for ML Models
Includes hyperparameter tuning, feature engineering, and ensemble methods
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif, RFE
from sklearn.impute import SimpleImputer
from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedKFold
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """Feature engineering for improved accuracy"""
    
    def __init__(self):
        self.scaler = None
        self.feature_selector = None
        self.imputer = None
        self.pca = None
        self.selected_features = None
        
    def preprocess_features(
        self,
        X_train: pd.DataFrame,
        X_val: Optional[pd.DataFrame] = None,
        X_test: Optional[pd.DataFrame] = None,
        scaling: str = 'standard',
        handle_missing: bool = True,
        feature_selection: Optional[str] = None,
        n_features: Optional[int] = None,
        use_pca: bool = False,
        pca_components: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Preprocess features for better accuracy
        
        Args:
            scaling: 'standard', 'robust', 'minmax', or None
            feature_selection: 'kbest', 'rfe', or None
            n_features: Number of features to select
            use_pca: Whether to use PCA for dimensionality reduction
        """
        # Handle missing values
        if handle_missing:
            self.imputer = SimpleImputer(strategy='median')
            X_train_processed = pd.DataFrame(
                self.imputer.fit_transform(X_train),
                columns=X_train.columns,
                index=X_train.index
            )
            if X_val is not None:
                X_val_processed = pd.DataFrame(
                    self.imputer.transform(X_val),
                    columns=X_val.columns,
                    index=X_val.index
                )
            else:
                X_val_processed = None
            if X_test is not None:
                X_test_processed = pd.DataFrame(
                    self.imputer.transform(X_test),
                    columns=X_test.columns,
                    index=X_test.index
                )
            else:
                X_test_processed = None
        else:
            X_train_processed = X_train.copy()
            X_val_processed = X_val.copy() if X_val is not None else None
            X_test_processed = X_test.copy() if X_test is not None else None
        
        # Feature scaling
        if scaling == 'standard':
            self.scaler = StandardScaler()
        elif scaling == 'robust':
            self.scaler = RobustScaler()
        elif scaling == 'minmax':
            self.scaler = MinMaxScaler()
        else:
            self.scaler = None
            
        if self.scaler:
            X_train_processed = pd.DataFrame(
                self.scaler.fit_transform(X_train_processed),
                columns=X_train_processed.columns,
                index=X_train_processed.index
            )
            if X_val_processed is not None:
                X_val_processed = pd.DataFrame(
                    self.scaler.transform(X_val_processed),
                    columns=X_val_processed.columns,
                    index=X_val_processed.index
                )
            if X_test_processed is not None:
                X_test_processed = pd.DataFrame(
                    self.scaler.transform(X_test_processed),
                    columns=X_test_processed.columns,
                    index=X_test_processed.index
                )
        
        # Feature selection
        if feature_selection and n_features:
            if feature_selection == 'kbest':
                self.feature_selector = SelectKBest(score_func=f_classif, k=min(n_features, X_train_processed.shape[1]))
            elif feature_selection == 'rfe':
                # RFE will be set with a model later
                pass
            
            if self.feature_selector:
                # Note: y_train needed for feature selection, will be handled separately
                pass
        
        # PCA for dimensionality reduction
        if use_pca and pca_components:
            n_components = min(pca_components, X_train_processed.shape[1])
            self.pca = PCA(n_components=n_components)
            X_train_processed = pd.DataFrame(
                self.pca.fit_transform(X_train_processed),
                index=X_train_processed.index
            )
            if X_val_processed is not None:
                X_val_processed = pd.DataFrame(
                    self.pca.transform(X_val_processed),
                    index=X_val_processed.index
                )
            if X_test_processed is not None:
                X_test_processed = pd.DataFrame(
                    self.pca.transform(X_test_processed),
                    index=X_test_processed.index
                )
        
        return X_train_processed, X_val_processed, X_test_processed
    
    def select_features(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        method: str = 'kbest',
        n_features: Optional[int] = None,
        model=None
    ) -> List[str]:
        """Select best features"""
        if n_features is None:
            n_features = min(50, X_train.shape[1])
        
        if method == 'kbest':
            self.feature_selector = SelectKBest(score_func=f_classif, k=n_features)
            X_selected = self.feature_selector.fit_transform(X_train, y_train)
            self.selected_features = X_train.columns[self.feature_selector.get_support()].tolist()
        elif method == 'mutual_info':
            self.feature_selector = SelectKBest(score_func=mutual_info_classif, k=n_features)
            X_selected = self.feature_selector.fit_transform(X_train, y_train)
            self.selected_features = X_train.columns[self.feature_selector.get_support()].tolist()
        elif method == 'rfe' and model is not None:
            self.feature_selector = RFE(estimator=model, n_features_to_select=n_features)
            self.feature_selector.fit(X_train, y_train)
            self.selected_features = X_train.columns[self.feature_selector.get_support()].tolist()
        else:
            self.selected_features = X_train.columns.tolist()
        
        return self.selected_features


class HyperparameterTuner:
    """Hyperparameter tuning for improved accuracy"""
    
    @staticmethod
    def get_optimal_hyperparameters(model_type: str) -> Dict[str, Any]:
        """Get optimized default hyperparameters for each model type"""
        optimal_params = {
            'LogisticRegression': {
                'C': 1.0,
                'penalty': 'l2',
                'solver': 'lbfgs',
                'max_iter': 2000,
                'class_weight': 'balanced',
                'random_state': 42
            },
            'RandomForest': {
                'n_estimators': 200,
                'max_depth': 15,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'max_features': 'sqrt',
                'class_weight': 'balanced',
                'random_state': 42,
                'n_jobs': -1
            },
            'XGBoost': {
                'n_estimators': 200,
                'max_depth': 8,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 3,
                'gamma': 0.1,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'random_state': 42,
                'eval_metric': 'logloss',
                'use_label_encoder': False
            },
            'LightGBM': {
                'n_estimators': 200,
                'max_depth': 12,
                'learning_rate': 0.05,
                'num_leaves': 31,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_samples': 20,
                'reg_alpha': 0.1,
                'reg_lambda': 0.1,
                'random_state': 42,
                'verbose': -1
            },
            'NeuralNetwork': {
                'hidden_layers': [128, 64, 32],
                'activation': 'relu',
                'dropout_rate': 0.3,
                'learning_rate': 0.001,
                'batch_size': 32,
                'epochs': 100,
                'optimizer': 'adam'
            }
        }
        return optimal_params.get(model_type, {})
    
    @staticmethod
    def get_search_space(model_type: str) -> Dict[str, List]:
        """Get hyperparameter search space for grid/random search"""
        search_spaces = {
            'LogisticRegression': {
                'C': [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                'penalty': ['l1', 'l2'],
                'solver': ['liblinear', 'lbfgs']
            },
            'RandomForest': {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 15, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2', None]
            },
            'XGBoost': {
                'n_estimators': [100, 200, 300],
                'max_depth': [6, 8, 10],
                'learning_rate': [0.01, 0.05, 0.1],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9]
            },
            'LightGBM': {
                'n_estimators': [100, 200, 300],
                'max_depth': [8, 10, 12],
                'learning_rate': [0.01, 0.05, 0.1],
                'num_leaves': [31, 50, 70],
                'subsample': [0.7, 0.8, 0.9]
            }
        }
        return search_spaces.get(model_type, {})
    
    def tune_hyperparameters(
        self,
        model,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        model_type: str,
        method: str = 'random',  # 'grid' or 'random'
        cv: int = 5,
        n_iter: int = 20
    ) -> Dict[str, Any]:
        """
        Tune hyperparameters using GridSearchCV or RandomizedSearchCV
        
        Returns:
            Best parameters and best score
        """
        search_space = self.get_search_space(model_type)
        
        if not search_space:
            return {'best_params': {}, 'best_score': 0.0}
        
        cv_fold = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
        
        if method == 'grid':
            search = GridSearchCV(
                estimator=model,
                param_grid=search_space,
                cv=cv_fold,
                scoring='accuracy',
                n_jobs=-1,
                verbose=0
            )
        else:  # random
            search = RandomizedSearchCV(
                estimator=model,
                param_distributions=search_space,
                n_iter=n_iter,
                cv=cv_fold,
                scoring='accuracy',
                n_jobs=-1,
                verbose=0,
                random_state=42
            )
        
        search.fit(X_train, y_train)
        
        return {
            'best_params': search.best_params_,
            'best_score': search.best_score_,
            'best_model': search.best_estimator_
        }


class EnsembleBuilder:
    """Build ensemble models for improved accuracy"""
    
    @staticmethod
    def create_voting_ensemble(
        models: List[Any],
        voting: str = 'soft'
    ) -> VotingClassifier:
        """Create voting ensemble from multiple models"""
        estimators = [(f"model_{i}", model) for i, model in enumerate(models)]
        return VotingClassifier(estimators=estimators, voting=voting)
    
    @staticmethod
    def create_stacking_ensemble(
        base_models: List[Any],
        meta_model: Any,
        cv: int = 5
    ) -> StackingClassifier:
        """Create stacking ensemble"""
        estimators = [(f"model_{i}", model) for i, model in enumerate(base_models)]
        return StackingClassifier(
            estimators=estimators,
            final_estimator=meta_model,
            cv=cv,
            stack_method='predict_proba'
        )


class AccuracyOptimizer:
    """Main class for optimizing ML model accuracy"""
    
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.hyperparameter_tuner = HyperparameterTuner()
        self.ensemble_builder = EnsembleBuilder()
    
    def optimize_model_accuracy(
        self,
        model,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        model_type: str = 'RandomForest',
        enable_feature_engineering: bool = True,
        enable_hyperparameter_tuning: bool = True,
        enable_ensemble: bool = False,
        other_models: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive accuracy optimization pipeline
        
        Returns:
            Dictionary with optimized model, metrics, and improvements
        """
        improvements = []
        original_score = 0.0
        optimized_score = 0.0
        
        # Step 1: Feature Engineering
        if enable_feature_engineering:
            X_train_opt, X_val_opt, _ = self.feature_engineer.preprocess_features(
                X_train,
                X_val,
                scaling='standard',
                handle_missing=True
            )
        else:
            X_train_opt = X_train
            X_val_opt = X_val
        
        # Step 2: Get optimal hyperparameters
        optimal_params = self.hyperparameter_tuner.get_optimal_hyperparameters(model_type)
        
        # Step 3: Update model with optimal parameters
        if optimal_params and hasattr(model, 'set_params'):
            model.set_params(**optimal_params)
        
        # Step 4: Train and evaluate original model
        if X_val is not None and y_val is not None:
            model.fit(X_train_opt, y_train)
            original_score = model.score(X_val_opt, y_val)
        
        # Step 5: Hyperparameter tuning
        if enable_hyperparameter_tuning:
            tuning_result = self.hyperparameter_tuner.tune_hyperparameters(
                model,
                X_train_opt,
                y_train,
                model_type,
                method='random',
                n_iter=20
            )
            
            if tuning_result['best_model'] is not None:
                model = tuning_result['best_model']
                optimized_score = tuning_result['best_score']
                improvements.append(f"Hyperparameter tuning improved score by {optimized_score - original_score:.4f}")
        
        # Step 6: Ensemble methods
        if enable_ensemble and other_models:
            ensemble = self.ensemble_builder.create_voting_ensemble(
                [model] + other_models,
                voting='soft'
            )
            ensemble.fit(X_train_opt, y_train)
            if X_val_opt is not None and y_val is not None:
                ensemble_score = ensemble.score(X_val_opt, y_val)
                if ensemble_score > optimized_score:
                    model = ensemble
                    optimized_score = ensemble_score
                    improvements.append(f"Ensemble improved score by {ensemble_score - optimized_score:.4f}")
        
        return {
            'optimized_model': model,
            'original_score': original_score,
            'optimized_score': optimized_score,
            'improvement': optimized_score - original_score,
            'improvements': improvements,
            'optimal_hyperparameters': optimal_params
        }
