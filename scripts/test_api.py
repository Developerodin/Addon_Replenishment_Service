"""
Test script for the replenishment service API.
Tests all endpoints to ensure they work correctly.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from loguru import logger


class APITester:
    """Test class for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def test_health_check(self):
        """Test health check endpoint."""
        logger.info("Testing health check endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "database_connected" in data
            assert "model_loaded" in data
            
            logger.info(f"Health check passed: {data['status']}")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def test_predict_forecast(self):
        """Test prediction endpoint."""
        logger.info("Testing prediction endpoint...")
        
        try:
            # Sample prediction request
            request_data = {
                "store_id": "store_001",
                "product_id": "product_001",
                "forecast_month": (datetime.now() + timedelta(days=30)).isoformat(),
                "historical_months": 12
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/predict-forecast",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "prediction_id" in data
                assert "predicted_quantity" in data
                assert "confidence_score" in data
                
                logger.info(f"Prediction successful: {data['predicted_quantity']} units")
                return data["prediction_id"]
            else:
                logger.warning(f"Prediction failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Prediction test failed: {e}")
            return None
    
    async def test_get_prediction(self, prediction_id: str):
        """Test get prediction endpoint."""
        logger.info(f"Testing get prediction endpoint for ID: {prediction_id}")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/predictions/{prediction_id}")
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "store_id" in data
                assert "product_id" in data
                
                logger.info("Get prediction successful")
                return True
            else:
                logger.warning(f"Get prediction failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Get prediction test failed: {e}")
            return False
    
    async def test_get_predictions_by_store(self):
        """Test get predictions by store endpoint."""
        logger.info("Testing get predictions by store endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/predictions/store/store_001")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                
                logger.info(f"Get predictions by store successful: {len(data)} predictions")
                return True
            else:
                logger.warning(f"Get predictions by store failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Get predictions by store test failed: {e}")
            return False
    
    async def test_update_prediction(self, prediction_id: str):
        """Test update prediction endpoint."""
        logger.info(f"Testing update prediction endpoint for ID: {prediction_id}")
        
        try:
            update_data = {
                "actual_quantity": 150,
                "accuracy": 0.85
            }
            
            response = await self.client.put(
                f"{self.base_url}/api/v1/predictions/{prediction_id}",
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "message" in data
                
                logger.info("Update prediction successful")
                return True
            else:
                logger.warning(f"Update prediction failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Update prediction test failed: {e}")
            return False
    
    async def test_get_accuracy_stats(self):
        """Test accuracy stats endpoint."""
        logger.info("Testing accuracy stats endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/stats/accuracy")
            
            if response.status_code == 200:
                data = response.json()
                assert "total_predictions" in data
                assert "avg_accuracy" in data
                
                logger.info(f"Accuracy stats successful: {data['total_predictions']} predictions")
                return True
            else:
                logger.warning(f"Accuracy stats failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Accuracy stats test failed: {e}")
            return False
    
    async def test_model_info(self):
        """Test model info endpoint."""
        logger.info("Testing model info endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/model/info")
            
            if response.status_code == 200:
                data = response.json()
                assert "model_version" in data
                assert "metrics" in data
                
                logger.info(f"Model info successful: {data['model_version']}")
                return True
            else:
                logger.warning(f"Model info failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Model info test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all API tests."""
        logger.info("Starting API tests...")
        
        results = {}
        
        # Test health check
        results["health_check"] = await self.test_health_check()
        
        # Test prediction
        prediction_id = await self.test_predict_forecast()
        results["predict_forecast"] = prediction_id is not None
        
        if prediction_id:
            # Test get prediction
            results["get_prediction"] = await self.test_get_prediction(prediction_id)
            
            # Test update prediction
            results["update_prediction"] = await self.test_update_prediction(prediction_id)
        
        # Test other endpoints
        results["get_predictions_by_store"] = await self.test_get_predictions_by_store()
        results["accuracy_stats"] = await self.test_get_accuracy_stats()
        results["model_info"] = await self.test_model_info()
        
        # Print results
        logger.info("API Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
        
        return results
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main test function."""
    tester = APITester()
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main()) 