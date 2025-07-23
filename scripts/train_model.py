"""
Script to train the XGBoost model for replenishment forecasting.
This script fetches data from Node.js API and trains the model.
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

from app.config import settings
from app.database.connection import db_manager
from app.services.data_service import data_service
from app.services.ml_service import ml_service


async def train_model():
    """Train the XGBoost model with historical data."""
    try:
        logger.info("Starting model training...")
        
        # Connect to database
        await db_manager.connect()
        
        # Get actual store and product IDs from Node.js API
        all_stores = await data_service.fetch_all_stores()
        logger.info(f"Found {len(all_stores)} stores in the system")
        
        # Use first few stores for training (to avoid too much data)
        sample_stores = all_stores[:3] if len(all_stores) >= 3 else all_stores
        logger.info(f"Using {len(sample_stores)} stores for training: {sample_stores}")
        
        sample_products = []
        for store_id in sample_stores:
            store_products = await data_service.fetch_store_products(store_id)
            # Use more products per store to get more data
            sample_products.extend(store_products[:5])  # Use first 5 products
        
        # Remove duplicates
        sample_products = list(set(sample_products))
        logger.info(f"Using {len(sample_products)} unique products for training")
        
        all_sales_data = []
        
        # Fetch data for sample stores and products
        for store_id in sample_stores:
            for product_id in sample_products:
                try:
                    # Calculate date range (last 12 months)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365)
                    
                    sales_data = await data_service.fetch_sales_data(
                        store_id, product_id, start_date, end_date
                    )
                    
                    if sales_data:
                        all_sales_data.extend(sales_data)
                        logger.info(f"Fetched {len(sales_data)} records for {store_id}/{product_id}")
                    else:
                        logger.warning(f"No data found for {store_id}/{product_id}")
                        
                except Exception as e:
                    logger.error(f"Error fetching data for {store_id}/{product_id}: {e}")
                    continue
        
        if not all_sales_data:
            logger.error("No sales data available for training")
            return
        
        logger.info(f"Total sales records collected: {len(all_sales_data)}")
        
        # Prepare features data
        features_df = data_service.prepare_features_data(all_sales_data)
        
        if len(features_df) == 0:
            logger.error("No features data available after preprocessing")
            return
        
        logger.info(f"Features data prepared: {len(features_df)} rows, {len(features_df.columns)} columns")
        
        # Train model
        model_info = ml_service.train_model(features_df)
        
        logger.info("Model training completed successfully!")
        logger.info(f"Model version: {model_info.model_version}")
        logger.info(f"Training metrics: MAE={model_info.metrics.mae:.2f}, MAPE={model_info.metrics.mape:.2f}%")
        
        # Print feature importance
        logger.info("Top 10 feature importance:")
        for feature in model_info.feature_importance[:10]:
            logger.info(f"  {feature.feature_name}: {feature.importance_score:.4f}")
        
    except Exception as e:
        logger.error(f"Error during model training: {e}")
        raise
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(train_model()) 