"""
Machine Learning service for XGBoost model operations.
Handles model training, prediction, and evaluation.
"""

import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
from loguru import logger
from app.config import settings
from app.models.schemas import ModelMetrics, FeatureImportance, ModelInfo


class MLService:
    """Service for machine learning operations with XGBoost."""
    
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_columns = []
        self.model_version = None
        self.training_date = None
        self.metrics = None
        
        # Ensure models directory exists
        os.makedirs(os.path.dirname(settings.model_path), exist_ok=True)
    
    def train_model(self, df: pd.DataFrame) -> ModelInfo:
        """
        Train XGBoost model on prepared features data.
        
        Args:
            df: DataFrame with features and target
            
        Returns:
            ModelInfo with training results
        """
        try:
            # Prepare features and target
            feature_cols = self._get_numeric_features(df)
            X = df[feature_cols]
            y = df['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train XGBoost model
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = self.model.predict(X_test)
            
            # Calculate metrics
            self.metrics = self._calculate_metrics(y_test, y_pred)
            
            # Update model info
            self.model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.training_date = datetime.now()
            self.feature_columns = feature_cols
            
            # Save model
            self._save_model()
            
            # Create feature importance
            feature_importance = self._get_feature_importance()
            
            model_info = ModelInfo(
                model_version=self.model_version,
                training_date=self.training_date,
                features_count=len(feature_cols),
                training_samples=len(X_train),
                metrics=self.metrics,
                feature_importance=feature_importance
            )
            
            logger.info(f"Model trained successfully. Version: {self.model_version}")
            return model_info
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def predict(self, features: pd.DataFrame) -> Tuple[int, float]:
        """
        Make prediction using trained model.
        
        Args:
            features: DataFrame with features for prediction
            
        Returns:
            Tuple of (predicted_quantity, confidence_score)
        """
        if self.model is None:
            self._load_model()
        
        if self.model is None:
            raise ValueError("No trained model available")
        
        try:
            # Ensure features match training features
            feature_cols = self._get_numeric_features(features)
            X = features[feature_cols]
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            
            # Calculate confidence score (using model's feature importance)
            confidence = self._calculate_confidence(X)
            
            return int(max(0, round(prediction))), confidence
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def _get_numeric_features(self, df: pd.DataFrame) -> list:
        """Get numeric feature columns for model training."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove target and non-feature columns
        exclude_cols = ['target', 'quantity', 'revenue']
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        return feature_cols
    
    def _calculate_metrics(self, y_true: pd.Series, y_pred: np.ndarray) -> ModelMetrics:
        """Calculate model performance metrics."""
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        # Calculate MAPE
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        return ModelMetrics(
            mae=mae,
            mape=mape,
            rmse=rmse,
            r2_score=r2,
            training_date=self.training_date,
            model_version=self.model_version
        )
    
    def _get_feature_importance(self) -> list:
        """Get feature importance from trained model."""
        if self.model is None:
            return []
        
        importance_scores = self.model.feature_importances_
        feature_names = self.model.feature_names_in_
        
        # Create feature importance list
        feature_importance = []
        for i, (name, score) in enumerate(zip(feature_names, importance_scores)):
            feature_importance.append(FeatureImportance(
                feature_name=name,
                importance_score=float(score),
                rank=i + 1
            ))
        
        # Sort by importance
        feature_importance.sort(key=lambda x: x.importance_score, reverse=True)
        
        return feature_importance
    
    def _calculate_confidence(self, X: pd.DataFrame) -> float:
        """Calculate confidence score for prediction."""
        # Simple confidence based on feature values
        # In production, you might use model uncertainty or ensemble methods
        
        # Check if features are within expected ranges
        feature_ranges = {
            'month': (1, 12),
            'year': (2020, 2030),
            'day_of_week': (0, 6),
            'quarter': (1, 4)
        }
        
        confidence = 1.0
        
        for col, (min_val, max_val) in feature_ranges.items():
            if col in X.columns:
                value = X[col].iloc[0]
                if min_val <= value <= max_val:
                    confidence *= 0.95
                else:
                    confidence *= 0.5
        
        return max(0.1, min(1.0, confidence))
    
    def _save_model(self):
        """Save trained model to disk."""
        try:
            model_data = {
                'model': self.model,
                'feature_columns': self.feature_columns,
                'model_version': self.model_version,
                'training_date': self.training_date,
                'metrics': self.metrics
            }
            
            joblib.dump(model_data, settings.model_path)
            logger.info(f"Model saved to {settings.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def _load_model(self):
        """Load trained model from disk."""
        try:
            if os.path.exists(settings.model_path):
                model_data = joblib.load(settings.model_path)
                
                self.model = model_data['model']
                self.feature_columns = model_data['feature_columns']
                self.model_version = model_data['model_version']
                self.training_date = model_data['training_date']
                self.metrics = model_data['metrics']
                
                logger.info(f"Model loaded from {settings.model_path}")
            else:
                logger.warning("No saved model found")
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready for prediction."""
        if self.model is None:
            self._load_model()
        return self.model is not None
    
    def get_model_info(self) -> Optional[ModelInfo]:
        """Get current model information."""
        if not self.is_model_loaded():
            return None
        
        feature_importance = self._get_feature_importance()
        
        return ModelInfo(
            model_version=self.model_version,
            training_date=self.training_date,
            features_count=len(self.feature_columns),
            training_samples=0,  # Not stored in saved model
            metrics=self.metrics,
            feature_importance=feature_importance
        )


# Global ML service instance
ml_service = MLService() 