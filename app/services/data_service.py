"""
Data service for fetching and processing data from Node.js API.
Handles data retrieval, transformation, and storage operations.
"""

import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
from app.config import settings
from app.models.schemas import SalesData


class DataService:
    """Service for handling data operations with Node.js API."""
    
    def __init__(self):
        self.base_url = settings.nodejs_api_base_url
        self.api_key = settings.nodejs_api_key
        self.headers = {}
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            self.headers["Content-Type"] = "application/json"
    
    async def fetch_sales_data(
        self, 
        store_id: str, 
        product_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[SalesData]:
        """
        Fetch sales data from Node.js API for specific store and product.
        
        Args:
            store_id: Store identifier
            product_id: Product identifier
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            List of SalesData objects
        """
        try:
            async with httpx.AsyncClient() as client:
                # Node.js API doesn't use query params, we'll filter after fetching
                response = await client.get(
                    f"{self.base_url}/sales",
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Convert to SalesData objects and filter by store_id and product_id
                sales_data = []
                for item in data.get("results", []):
                    # Extract store_id and product_id from nested structure
                    item_store_id = item.get("plant", {}).get("storeId")
                    item_product_id = item.get("materialCode", {}).get("styleCode")
                    
                    # Filter by store_id and product_id
                    if item_store_id == store_id and item_product_id == product_id:
                        # Convert Node.js format to SalesData format
                        sales_item = {
                            "store_id": item_store_id,
                            "product_id": item_product_id,
                            "date": datetime.fromisoformat(item["date"].replace("Z", "+00:00")),
                            "quantity": item["quantity"],
                            "revenue": item["nsv"],  # Using NSV as revenue
                            "discount": item.get("discount", 0.0),
                            "is_festival": False  # Default value, can be enhanced later
                        }
                        sales_data.append(SalesData(**sales_item))
                
                logger.info(f"Fetched {len(sales_data)} sales records for {store_id}/{product_id}")
                return sales_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching sales data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching sales data: {e}")
            raise
    
    async def fetch_store_products(self, store_id: str) -> List[str]:
        """
        Fetch all products for a specific store from sales data.
        
        Args:
            store_id: Store identifier
            
        Returns:
            List of product IDs
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sales",
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract unique product IDs for the given store
                product_ids = set()
                for item in data.get("results", []):
                    item_store_id = item.get("plant", {}).get("storeId")
                    if item_store_id == store_id:
                        product_id = item.get("materialCode", {}).get("styleCode")
                        if product_id:
                            product_ids.add(product_id)
                
                logger.info(f"Found {len(product_ids)} products for store {store_id}")
                return list(product_ids)
                
        except Exception as e:
            logger.error(f"Error fetching store products: {e}")
            raise
    
    async def fetch_all_stores(self) -> List[str]:
        """
        Fetch all unique store IDs from sales data.
        
        Returns:
            List of store IDs
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sales",
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract unique store IDs
                store_ids = set()
                for item in data.get("results", []):
                    store_id = item.get("plant", {}).get("storeId")
                    if store_id:
                        store_ids.add(store_id)
                
                logger.info(f"Found {len(store_ids)} unique stores")
                return list(store_ids)
                
        except Exception as e:
            logger.error(f"Error fetching stores: {e}")
            raise
    
    def prepare_features_data(self, sales_data: List[SalesData]) -> pd.DataFrame:
        """
        Prepare features data for model training.
        
        Args:
            sales_data: List of sales data
            
        Returns:
            DataFrame with engineered features
        """
        if not sales_data:
            raise ValueError("No sales data provided")
        
        if len(sales_data) < 5:
            logger.warning(f"Very little data available ({len(sales_data)} records). Model may not perform well.")
        
        # Convert to DataFrame
        df = pd.DataFrame([sale.dict() for sale in sales_data])
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date')
        
        # Create features
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['day_of_week'] = df['date'].dt.dayofweek
        df['quarter'] = df['date'].dt.quarter
        
        # Lag features (previous months sales)
        for i in range(1, 4):
            df[f'sales_lag_{i}_month'] = df.groupby(['store_id', 'product_id'])['quantity'].shift(i).fillna(0)
        
        # Rolling averages (simplified for small datasets)
        for window in [3, 6, 12]:
            df[f'sales_rolling_{window}_month'] = df['quantity']  # Use current quantity for small datasets
        
        # Discount features
        df['avg_discount'] = df.groupby(['store_id', 'product_id'])['discount'].transform('mean')
        df['discount_std'] = df.groupby(['store_id', 'product_id'])['discount'].transform('std')
        
        # Festival features
        df['is_festival_month'] = df['is_festival'].astype(int)
        
        # Target variable (next month's sales)
        df['target'] = df.groupby(['store_id', 'product_id'])['quantity'].shift(-1)
        
        # For very small datasets, use current quantity as target if no future data
        if len(df) < 10:
            df['target'] = df['target'].fillna(df['quantity'])
        
        # Remove rows with NaN values (but be more lenient for small datasets)
        if len(df) < 10:
            # Only remove rows where essential features are missing
            df = df.dropna(subset=['quantity', 'date'])
        else:
            df = df.dropna()
        
        logger.info(f"Prepared features data with {len(df)} rows and {len(df.columns)} features")
        return df
    
    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns for model training."""
        return [
            'store_id', 'product_id', 'month', 'year', 'day_of_week', 'quarter',
            'sales_lag_1_month', 'sales_lag_2_month', 'sales_lag_3_month',
            'sales_rolling_3_month', 'sales_rolling_6_month', 'sales_rolling_12_month',
            'avg_discount', 'discount_std', 'is_festival_month'
        ]


# Global data service instance
data_service = DataService() 