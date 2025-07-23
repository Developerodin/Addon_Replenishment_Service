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
        self.collection = None
    
    async def _get_collection(self):
        """Get database collection, ensuring connection."""
        if self.collection is None:
            await db_manager.connect()
            self.collection = db_manager.collection
        return self.collection
    
    async def create_prediction(self, prediction: PredictionCreate) -> str:
        """
        Create a new prediction record.
        
        Args:
            prediction: Prediction data to create
            
        Returns:
            Created prediction ID
        """
        try:
            collection = await self._get_collection()
            prediction_dict = prediction.dict()
            prediction_dict['created_at'] = datetime.utcnow()
            
            result = await collection.insert_one(prediction_dict)
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
            # Validate ObjectId format
            if not ObjectId.is_valid(prediction_id):
                logger.warning(f"Invalid ObjectId format: {prediction_id}")
                return None
                
            collection = await self._get_collection()
            prediction_dict = await collection.find_one({"_id": ObjectId(prediction_id)})
            
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
            collection = await self._get_collection()
            cursor = collection.find({"store_id": store_id}).sort("created_at", -1).limit(limit)
            
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
            collection = await self._get_collection()
            cursor = collection.find({"product_id": product_id}).sort("created_at", -1).limit(limit)
            
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
            collection = await self._get_collection()
            cursor = collection.find({
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
            # Validate ObjectId format
            if not ObjectId.is_valid(prediction_id):
                logger.warning(f"Invalid ObjectId format: {prediction_id}")
                return False
                
            update_dict = update_data.dict(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            collection = await self._get_collection()
            result = await collection.update_one(
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
            # Validate ObjectId format
            if not ObjectId.is_valid(prediction_id):
                logger.warning(f"Invalid ObjectId format: {prediction_id}")
                return False
                
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": ObjectId(prediction_id)})
            
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
            # First get total predictions count
            total_filter = {}
            if store_id:
                total_filter["store_id"] = store_id
                
            collection = await self._get_collection()
            total_predictions = await collection.count_documents(total_filter)
            
            # Get predictions with actual data
            match_filter = {"actual_quantity": {"$exists": True, "$ne": None}}
            if store_id:
                match_filter["store_id"] = store_id
            
            pipeline = [
                {"$match": match_filter},
                {"$group": {
                    "_id": None,
                    "predictions_with_actual": {"$sum": 1},
                    "avg_accuracy": {"$avg": "$accuracy"},
                    "min_accuracy": {"$min": "$accuracy"},
                    "max_accuracy": {"$max": "$accuracy"},
                    "avg_mape": {"$avg": {"$abs": {"$divide": [
                        {"$subtract": ["$predicted_quantity", "$actual_quantity"]},
                        {"$max": ["$actual_quantity", 1]}  # Avoid division by zero
                    ]}}}
                }}
            ]
            
            result = await collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_predictions": total_predictions,
                    "predictions_with_actual": stats["predictions_with_actual"],
                    "average_accuracy": round(stats["avg_accuracy"], 4) if stats["avg_accuracy"] else 0,
                    "min_accuracy": round(stats["min_accuracy"], 4) if stats["min_accuracy"] else 0,
                    "max_accuracy": round(stats["max_accuracy"], 4) if stats["max_accuracy"] else 0,
                    "avg_mape": round(stats["avg_mape"] * 100, 2) if stats["avg_mape"] else 0
                }
            
            return {
                "total_predictions": total_predictions,
                "predictions_with_actual": 0,
                "average_accuracy": 0,
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
            collection = await self._get_collection()
            
            # Use aggregation pipeline for better error handling
            pipeline = [
                {"$sort": {"created_at": -1}},
                {"$limit": limit},
                {"$addFields": {"id": {"$toString": "$_id"}}},
                {"$project": {"_id": 0}}
            ]
            
            cursor = collection.aggregate(pipeline)
            predictions = []
            
            async for prediction_dict in cursor:
                try:
                    predictions.append(PredictionInDB(**prediction_dict))
                except Exception as parse_error:
                    logger.warning(f"Error parsing prediction: {parse_error}")
                    continue
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            raise


# Global prediction repository instance
prediction_repository = PredictionRepository() 