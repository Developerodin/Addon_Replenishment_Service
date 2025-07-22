"""
FastAPI routes for the replenishment service.
Defines all API endpoints and their handlers.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger

from app.models.schemas import (
    PredictionRequest, PredictionResponse, PredictionCreate, 
    PredictionUpdate, PredictionInDB, ModelInfo, HealthCheck
)
from app.services.data_service import data_service
from app.services.ml_service import ml_service
from app.repositories.prediction_repository import prediction_repository
from app.database.connection import db_manager


# Create router
router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    try:
        db_connected = await db_manager.health_check()
        model_loaded = ml_service.is_model_loaded()
        
        return HealthCheck(
            status="healthy" if db_connected and model_loaded else "unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            database_connected=db_connected,
            model_loaded=model_loaded
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/predict-forecast", response_model=PredictionResponse)
async def predict_forecast(request: PredictionRequest):
    """
    Generate forecast prediction for store and product.
    
    Args:
        request: Prediction request with store, product, and forecast month
        
    Returns:
        Prediction response with forecasted quantity
    """
    try:
        # Calculate date range for historical data
        end_date = request.forecast_month - timedelta(days=1)
        start_date = end_date - timedelta(days=30 * request.historical_months)
        
        # Fetch historical sales data
        sales_data = await data_service.fetch_sales_data(
            request.store_id,
            request.product_id,
            start_date,
            end_date
        )
        
        if not sales_data:
            raise HTTPException(
                status_code=404,
                detail="No historical sales data found for the specified store and product"
            )
        
        # Prepare features for prediction
        features_df = data_service.prepare_features_data(sales_data)
        
        if len(features_df) == 0:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for prediction"
            )
        
        # Get the most recent features for prediction
        latest_features = features_df.iloc[-1:].copy()
        
        # Update features for forecast month
        latest_features['month'] = request.forecast_month.month
        latest_features['year'] = request.forecast_month.year
        latest_features['day_of_week'] = request.forecast_month.weekday()
        latest_features['quarter'] = (request.forecast_month.month - 1) // 3 + 1
        
        # Make prediction
        predicted_quantity, confidence_score = ml_service.predict(latest_features)
        
        # Get model info
        model_info = ml_service.get_model_info()
        model_version = model_info.model_version if model_info else "unknown"
        
        # Create prediction record
        prediction_data = PredictionCreate(
            store_id=request.store_id,
            product_id=request.product_id,
            forecast_month=request.forecast_month,
            predicted_quantity=predicted_quantity,
            confidence_score=confidence_score,
            model_version=model_version,
            features_used=data_service.get_feature_columns()
        )
        
        # Save to database
        prediction_id = await prediction_repository.create_prediction(prediction_data)
        
        # Return response
        return PredictionResponse(
            prediction_id=prediction_id,
            store_id=request.store_id,
            product_id=request.product_id,
            forecast_month=request.forecast_month,
            predicted_quantity=predicted_quantity,
            confidence_score=confidence_score,
            model_version=model_version,
            created_at=datetime.utcnow(),
            features_used=data_service.get_feature_columns()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in predict_forecast: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")


@router.get("/predictions/{prediction_id}", response_model=PredictionInDB)
async def get_prediction(prediction_id: str):
    """
    Get prediction by ID.
    
    Args:
        prediction_id: Prediction identifier
        
    Returns:
        Prediction data
    """
    try:
        prediction = await prediction_repository.get_prediction(prediction_id)
        
        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prediction")


@router.get("/predictions/store/{store_id}", response_model=List[PredictionInDB])
async def get_predictions_by_store(
    store_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get predictions for a specific store.
    
    Args:
        store_id: Store identifier
        limit: Maximum number of predictions to return
        
    Returns:
        List of predictions
    """
    try:
        predictions = await prediction_repository.get_predictions_by_store(store_id, limit)
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting predictions by store: {e}")
        raise HTTPException(status_code=500, detail="Failed to get predictions")


@router.get("/predictions/product/{product_id}", response_model=List[PredictionInDB])
async def get_predictions_by_product(
    product_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get predictions for a specific product.
    
    Args:
        product_id: Product identifier
        limit: Maximum number of predictions to return
        
    Returns:
        List of predictions
    """
    try:
        predictions = await prediction_repository.get_predictions_by_product(product_id, limit)
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting predictions by product: {e}")
        raise HTTPException(status_code=500, detail="Failed to get predictions")


@router.get("/predictions/store/{store_id}/product/{product_id}", response_model=List[PredictionInDB])
async def get_predictions_by_store_and_product(
    store_id: str,
    product_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get predictions for specific store and product combination.
    
    Args:
        store_id: Store identifier
        product_id: Product identifier
        limit: Maximum number of predictions to return
        
    Returns:
        List of predictions
    """
    try:
        predictions = await prediction_repository.get_predictions_by_store_and_product(
            store_id, product_id, limit
        )
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting predictions by store and product: {e}")
        raise HTTPException(status_code=500, detail="Failed to get predictions")


@router.put("/predictions/{prediction_id}")
async def update_prediction(prediction_id: str, update_data: PredictionUpdate):
    """
    Update prediction with actual data.
    
    Args:
        prediction_id: Prediction identifier
        update_data: Update data with actual quantity
        
    Returns:
        Success message
    """
    try:
        # Calculate accuracy if both predicted and actual quantities are provided
        if update_data.actual_quantity is not None:
            prediction = await prediction_repository.get_prediction(prediction_id)
            if prediction and prediction.predicted_quantity:
                accuracy = 1 - abs(prediction.predicted_quantity - update_data.actual_quantity) / update_data.actual_quantity
                update_data.accuracy = max(0, accuracy)
        
        success = await prediction_repository.update_prediction(prediction_id, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        return {"message": "Prediction updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prediction")


@router.delete("/predictions/{prediction_id}")
async def delete_prediction(prediction_id: str):
    """
    Delete prediction by ID.
    
    Args:
        prediction_id: Prediction identifier
        
    Returns:
        Success message
    """
    try:
        success = await prediction_repository.delete_prediction(prediction_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Prediction not found")
        
        return {"message": "Prediction deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete prediction")


@router.get("/predictions/recent", response_model=List[PredictionInDB])
async def get_recent_predictions(
    limit: int = Query(50, ge=1, le=1000)
):
    """
    Get recent predictions.
    
    Args:
        limit: Maximum number of predictions to return
        
    Returns:
        List of recent predictions
    """
    try:
        predictions = await prediction_repository.get_recent_predictions(limit)
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting recent predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent predictions")


@router.get("/stats/accuracy")
async def get_accuracy_stats(store_id: Optional[str] = None):
    """
    Get accuracy statistics for predictions.
    
    Args:
        store_id: Optional store filter
        
    Returns:
        Accuracy statistics
    """
    try:
        stats = await prediction_repository.get_accuracy_stats(store_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting accuracy stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get accuracy stats")


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    """
    Get current model information.
    
    Returns:
        Model information
    """
    try:
        model_info = ml_service.get_model_info()
        
        if not model_info:
            raise HTTPException(status_code=404, detail="No model information available")
        
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info") 