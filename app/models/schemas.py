"""
Pydantic schemas for data validation and API models.
Defines the structure of request/response data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SalesData(BaseModel):
    """Schema for sales data from Node.js API."""
    store_id: str
    product_id: str
    date: datetime
    quantity: int
    revenue: float
    discount: Optional[float] = 0.0
    is_festival: bool = False


class PredictionRequest(BaseModel):
    """Schema for prediction request."""
    store_id: str = Field(..., description="Store identifier")
    product_id: str = Field(..., description="Product identifier")
    forecast_month: datetime = Field(..., description="Month to forecast")
    historical_months: Optional[int] = Field(12, description="Number of historical months to use")


class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    prediction_id: str
    store_id: str
    product_id: str
    forecast_month: datetime
    predicted_quantity: int
    confidence_score: float
    model_version: str
    created_at: datetime
    features_used: List[str]


class PredictionCreate(BaseModel):
    """Schema for creating prediction record."""
    store_id: str
    product_id: str
    forecast_month: datetime
    predicted_quantity: int
    confidence_score: float
    model_version: str
    features_used: List[str]
    actual_quantity: Optional[int] = None
    accuracy: Optional[float] = None


class PredictionUpdate(BaseModel):
    """Schema for updating prediction record."""
    actual_quantity: Optional[int] = None
    accuracy: Optional[float] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PredictionInDB(PredictionCreate):
    """Schema for prediction in database."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class ModelMetrics(BaseModel):
    """Schema for model performance metrics."""
    mae: float
    mape: float
    rmse: float
    r2_score: float
    training_date: datetime
    model_version: str


class FeatureImportance(BaseModel):
    """Schema for feature importance data."""
    feature_name: str
    importance_score: float
    rank: int


class ModelInfo(BaseModel):
    """Schema for model information."""
    model_version: str
    training_date: datetime
    features_count: int
    training_samples: int
    metrics: ModelMetrics
    feature_importance: List[FeatureImportance]


class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    database_connected: bool
    model_loaded: bool 