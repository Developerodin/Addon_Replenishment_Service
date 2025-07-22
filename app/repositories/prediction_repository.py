"""
Prediction repository for database operations.
Handles CRUD operations for prediction data.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from loguru import logger
from app.database.connection import db_manager
from app.models.schemas import PredictionCreate, PredictionUpdate, PredictionInDB


class PredictionRepository:
    """Repository for prediction database operations."""
    
    def __init__(self):
        self.collection = db_manager.collection
    
    async def create_prediction(self, prediction: PredictionCreate) -> str:
        """
        Create a new prediction record.
        
        Args:
            prediction: Prediction data to create
            
        Returns:
            Created prediction ID
        """
        try:
            prediction_dict = prediction.dict()
            prediction_dict['created_at'] = datetime.utcnow()
            
            result = await self.collection.insert_one(prediction_dict)
            prediction_id = str(result.inserted_id)
            
            logger.info(f"Created prediction with ID: {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Error creating prediction: {e}")
            raise
    
    async def get_prediction(self, prediction_id: str) -> Optional[PredictionInDB]:
        """
        Get prediction by ID.
        
        Args:
            prediction_id: Prediction identifier
            
        Returns:
            Prediction data or None
        """
        try:
            prediction_dict = await self.collection.find_one({"_id": ObjectId(prediction_id)})
            
            if prediction_dict:
                prediction_dict['id'] = str(prediction_dict.pop('_id'))
                return PredictionInDB(**prediction_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting prediction: {e}")
            raise
    
    async def get_predictions_by_store(
        self, 
        store_id: str, 
        limit: int = 100
    ) -> List[PredictionInDB]:
        """
        Get predictions for a specific store.
        
        Args:
            store_id: Store identifier
            limit: Maximum number of predictions to return
            
        Returns:
            List of predictions
        """
        try:
            cursor = self.collection.find({"store_id": store_id}).sort("created_at", -1).limit(limit)
            
            predictions = []
            async for prediction_dict in cursor:
                prediction_dict['id'] = str(prediction_dict.pop('_id'))
                predictions.append(PredictionInDB(**prediction_dict))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting predictions by store: {e}")
            raise
    
    async def get_predictions_by_product(
        self, 
        product_id: str, 
        limit: int = 100
    ) -> List[PredictionInDB]:
        """
        Get predictions for a specific product.
        
        Args:
            product_id: Product identifier
            limit: Maximum number of predictions to return
            
        Returns:
            List of predictions
        """
        try:
            cursor = self.collection.find({"product_id": product_id}).sort("created_at", -1).limit(limit)
            
            predictions = []
            async for prediction_dict in cursor:
                prediction_dict['id'] = str(prediction_dict.pop('_id'))
                predictions.append(PredictionInDB(**prediction_dict))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting predictions by product: {e}")
            raise
    
    async def get_predictions_by_store_and_product(
        self, 
        store_id: str, 
        product_id: str, 
        limit: int = 100
    ) -> List[PredictionInDB]:
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
            cursor = self.collection.find({
                "store_id": store_id,
                "product_id": product_id
            }).sort("created_at", -1).limit(limit)
            
            predictions = []
            async for prediction_dict in cursor:
                prediction_dict['id'] = str(prediction_dict.pop('_id'))
                predictions.append(PredictionInDB(**prediction_dict))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting predictions by store and product: {e}")
            raise
    
    async def update_prediction(
        self, 
        prediction_id: str, 
        update_data: PredictionUpdate
    ) -> bool:
        """
        Update prediction with actual data.
        
        Args:
            prediction_id: Prediction identifier
            update_data: Update data
            
        Returns:
            True if updated successfully
        """
        try:
            update_dict = update_data.dict(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(prediction_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated prediction: {prediction_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating prediction: {e}")
            raise
    
    async def delete_prediction(self, prediction_id: str) -> bool:
        """
        Delete prediction by ID.
        
        Args:
            prediction_id: Prediction identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(prediction_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted prediction: {prediction_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting prediction: {e}")
            raise
    
    async def get_accuracy_stats(self, store_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get accuracy statistics for predictions.
        
        Args:
            store_id: Optional store filter
            
        Returns:
            Dictionary with accuracy statistics
        """
        try:
            match_filter = {"actual_quantity": {"$exists": True}}
            if store_id:
                match_filter["store_id"] = store_id
            
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "total_predictions": {"$sum": 1},
                    "avg_accuracy": {"$avg": "$accuracy"},
                    "min_accuracy": {"$min": "$accuracy"},
                    "max_accuracy": {"$max": "$accuracy"},
                    "avg_mape": {"$avg": {"$abs": {"$divide": [
                        {"$subtract": ["$predicted_quantity", "$actual_quantity"]},
                        "$actual_quantity"
                    ]}}}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_predictions": stats["total_predictions"],
                    "avg_accuracy": round(stats["avg_accuracy"], 4),
                    "min_accuracy": round(stats["min_accuracy"], 4),
                    "max_accuracy": round(stats["max_accuracy"], 4),
                    "avg_mape": round(stats["avg_mape"] * 100, 2)
                }
            
            return {
                "total_predictions": 0,
                "avg_accuracy": 0,
                "min_accuracy": 0,
                "max_accuracy": 0,
                "avg_mape": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting accuracy stats: {e}")
            raise
    
    async def get_recent_predictions(self, limit: int = 50) -> List[PredictionInDB]:
        """
        Get recent predictions.
        
        Args:
            limit: Maximum number of predictions to return
            
        Returns:
            List of recent predictions
        """
        try:
            cursor = self.collection.find().sort("created_at", -1).limit(limit)
            
            predictions = []
            async for prediction_dict in cursor:
                prediction_dict['id'] = str(prediction_dict.pop('_id'))
                predictions.append(PredictionInDB(**prediction_dict))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            raise


# Global prediction repository instance
prediction_repository = PredictionRepository() 