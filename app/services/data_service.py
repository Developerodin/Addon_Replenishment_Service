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
                params = {
                    "store_id": store_id,
                    "product_id": product_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
                response = await client.get(
                    f"{self.base_url}/sales",
                    params=params,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Convert to SalesData objects
                sales_data = []
                for item in data.get("sales", []):
                    sales_data.append(SalesData(**item))
                
                logger.info(f"Fetched {len(sales_data)} sales records")
                return sales_data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching sales data: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching sales data: {e}")
            raise
    
    async def fetch_store_products(self, store_id: str) -> List[str]:
        """
        Fetch all products for a specific store.
        
        Args:
            store_id: Store identifier
            
        Returns:
            List of product IDs
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/stores/{store_id}/products",
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                return data.get("products", [])
                
        except Exception as e:
            logger.error(f"Error fetching store products: {e}")
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
            df[f'sales_lag_{i}_month'] = df.groupby(['store_id', 'product_id'])['quantity'].shift(i)
        
        # Rolling averages
        for window in [3, 6, 12]:
            df[f'sales_rolling_{window}_month'] = df.groupby(['store_id', 'product_id'])['quantity'].rolling(
                window=window, min_periods=1
            ).mean().reset_index(0, drop=True)
        
        # Discount features
        df['avg_discount'] = df.groupby(['store_id', 'product_id'])['discount'].transform('mean')
        df['discount_std'] = df.groupby(['store_id', 'product_id'])['discount'].transform('std')
        
        # Festival features
        df['is_festival_month'] = df['is_festival'].astype(int)
        
        # Target variable (next month's sales)
        df['target'] = df.groupby(['store_id', 'product_id'])['quantity'].shift(-1)
        
        # Remove rows with NaN values
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