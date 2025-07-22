"""
MongoDB connection module for the replenishment service.
Handles database connection and provides async client.
"""

import motor.motor_asyncio
from pymongo import MongoClient
from loguru import logger
from app.config import settings


class DatabaseManager:
    """Manages MongoDB connections and provides database access."""
    
    def __init__(self):
        self.async_client: motor.motor_asyncio.AsyncIOMotorClient = None
        self.sync_client: MongoClient = None
        self.database = None
        self.collection = None
    
    async def connect(self):
        """Establish async connection to MongoDB."""
        try:
            self.async_client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await self.async_client.admin.command('ping')
            
            self.database = self.async_client[settings.mongodb_database]
            self.collection = self.database[settings.mongodb_collection]
            
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def connect_sync(self):
        """Establish sync connection to MongoDB (for model training)."""
        try:
            self.sync_client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            self.sync_client.admin.command('ping')
            
            logger.info(f"Sync connection to MongoDB established")
            
        except Exception as e:
            logger.error(f"Failed to establish sync connection to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections."""
        if self.async_client:
            self.async_client.close()
            logger.info("Async MongoDB connection closed")
        
        if self.sync_client:
            self.sync_client.close()
            logger.info("Sync MongoDB connection closed")
    
    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            await self.async_client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_sync_database(self):
        """Get sync database instance for model training."""
        if not self.sync_client:
            self.connect_sync()
        return self.sync_client[settings.mongodb_database]


# Global database manager instance
db_manager = DatabaseManager() 