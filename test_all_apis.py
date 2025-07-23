#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Replenishment Service
Tests all endpoints and identifies issues.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import httpx
from loguru import logger

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30.0

# Test data
TEST_STORE_ID = "20000"
TEST_PRODUCT_ID = "ASC1SALBC00347"
TEST_PREDICTION_ID = None  # Will be set after creating a prediction


class APITester:
    """Comprehensive API testing class."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.prediction_id = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=TIMEOUT)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def log_test(self, endpoint: str, method: str, status: int, success: bool, error: str = None):
        """Log test result."""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {method} {endpoint} - Status: {status}")
        if error:
            print(f"   Error: {error}")
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return response."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.session.request(method, url, **kwargs)
            return {
                "status": response.status_code,
                "data": response.json() if response.content else None,
                "headers": dict(response.headers),
                "success": 200 <= response.status_code < 300
            }
        except Exception as e:
            return {
                "status": 0,
                "data": None,
                "error": str(e),
                "success": False
            }
    
    async def test_health_check(self):
        """Test health check endpoint."""
        print("\n🔍 Testing Health Check...")
        
        result = await self.make_request("GET", "/health")
        
        if result["success"]:
            data = result["data"]
            print(f"   Status: {data.get('status')}")
            print(f"   Database Connected: {data.get('database_connected')}")
            print(f"   Model Loaded: {data.get('model_loaded')}")
            print(f"   Version: {data.get('version')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test("/health", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_model_info(self):
        """Test model info endpoint."""
        print("\n🔍 Testing Model Info...")
        
        result = await self.make_request("GET", "/model/info")
        
        if result["success"]:
            data = result["data"]
            print(f"   Model Version: {data.get('model_version')}")
            print(f"   Training Date: {data.get('training_date')}")
            print(f"   Features Count: {data.get('features_count')}")
            print(f"   Training Samples: {data.get('training_samples')}")
            
            metrics = data.get('metrics', {})
            print(f"   MAE: {metrics.get('mae')}")
            print(f"   MAPE: {metrics.get('mape')}")
            print(f"   RMSE: {metrics.get('rmse')}")
            print(f"   R² Score: {metrics.get('r2_score')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test("/model/info", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_predict_forecast(self):
        """Test forecast prediction endpoint."""
        print("\n🔍 Testing Predict Forecast...")
        
        forecast_date = datetime.now() + timedelta(days=30)
        payload = {
            "store_id": TEST_STORE_ID,
            "product_id": TEST_PRODUCT_ID,
            "forecast_month": forecast_date.isoformat(),
            "historical_months": 12
        }
        
        result = await self.make_request("POST", "/predict-forecast", json=payload)
        
        if result["success"]:
            data = result["data"]
            self.prediction_id = data.get("prediction_id")
            print(f"   Prediction ID: {self.prediction_id}")
            print(f"   Predicted Quantity: {data.get('predicted_quantity')}")
            print(f"   Confidence Score: {data.get('confidence_score')}")
            print(f"   Model Version: {data.get('model_version')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
            if result["data"]:
                print(f"   Response: {result['data']}")
        
        self.log_test("/predict-forecast", "POST", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_prediction_by_id(self):
        """Test get prediction by ID endpoint."""
        if not self.prediction_id:
            print("\n⚠️  Skipping Get Prediction by ID - no prediction ID available")
            return None
            
        print(f"\n🔍 Testing Get Prediction by ID: {self.prediction_id}...")
        
        result = await self.make_request("GET", f"/predictions/{self.prediction_id}")
        
        if result["success"]:
            data = result["data"]
            print(f"   Store ID: {data.get('store_id')}")
            print(f"   Product ID: {data.get('product_id')}")
            print(f"   Predicted Quantity: {data.get('predicted_quantity')}")
            print(f"   Created At: {data.get('created_at')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test(f"/predictions/{self.prediction_id}", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_predictions_by_store(self):
        """Test get predictions by store endpoint."""
        print(f"\n🔍 Testing Get Predictions by Store: {TEST_STORE_ID}...")
        
        result = await self.make_request("GET", f"/predictions/store/{TEST_STORE_ID}?limit=10")
        
        if result["success"]:
            data = result["data"]
            print(f"   Found {len(data)} predictions")
            if data:
                print(f"   Latest: {data[0].get('created_at')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test(f"/predictions/store/{TEST_STORE_ID}", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_predictions_by_product(self):
        """Test get predictions by product endpoint."""
        print(f"\n🔍 Testing Get Predictions by Product: {TEST_PRODUCT_ID}...")
        
        result = await self.make_request("GET", f"/predictions/product/{TEST_PRODUCT_ID}?limit=10")
        
        if result["success"]:
            data = result["data"]
            print(f"   Found {len(data)} predictions")
            if data:
                print(f"   Latest: {data[0].get('created_at')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test(f"/predictions/product/{TEST_PRODUCT_ID}", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_predictions_by_store_and_product(self):
        """Test get predictions by store and product endpoint."""
        print(f"\n🔍 Testing Get Predictions by Store and Product...")
        
        result = await self.make_request(
            "GET", 
            f"/predictions/store/{TEST_STORE_ID}/product/{TEST_PRODUCT_ID}?limit=10"
        )
        
        if result["success"]:
            data = result["data"]
            print(f"   Found {len(data)} predictions")
            if data:
                print(f"   Latest: {data[0].get('created_at')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test(f"/predictions/store/{TEST_STORE_ID}/product/{TEST_PRODUCT_ID}", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_recent_predictions(self):
        """Test get recent predictions endpoint."""
        print("\n🔍 Testing Get Recent Predictions...")
        
        result = await self.make_request("GET", "/predictions/recent?limit=10")
        
        if result["success"]:
            data = result["data"]
            print(f"   Found {len(data)} recent predictions")
            if data:
                print(f"   Latest: {data[0].get('created_at')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test("/predictions/recent", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_update_prediction(self):
        """Test update prediction endpoint."""
        if not self.prediction_id:
            print("\n⚠️  Skipping Update Prediction - no prediction ID available")
            return None
            
        print(f"\n🔍 Testing Update Prediction: {self.prediction_id}...")
        
        payload = {
            "actual_quantity": 150,
            "accuracy": 0.85
        }
        
        result = await self.make_request("PUT", f"/predictions/{self.prediction_id}", json=payload)
        
        if result["success"]:
            data = result["data"]
            print(f"   Message: {data.get('message')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
            if result["data"]:
                print(f"   Response: {result['data']}")
        
        self.log_test(f"/predictions/{self.prediction_id}", "PUT", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_accuracy_stats(self):
        """Test accuracy statistics endpoint."""
        print("\n🔍 Testing Get Accuracy Stats...")
        
        result = await self.make_request("GET", "/stats/accuracy")
        
        if result["success"]:
            data = result["data"]
            print(f"   Total Predictions: {data.get('total_predictions', 0)}")
            print(f"   Average Accuracy: {data.get('average_accuracy', 0)}")
            print(f"   Predictions with Actual Data: {data.get('predictions_with_actual', 0)}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test("/stats/accuracy", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_get_accuracy_stats_with_store(self):
        """Test accuracy statistics with store filter."""
        print(f"\n🔍 Testing Get Accuracy Stats with Store Filter: {TEST_STORE_ID}...")
        
        result = await self.make_request("GET", f"/stats/accuracy?store_id={TEST_STORE_ID}")
        
        if result["success"]:
            data = result["data"]
            print(f"   Total Predictions: {data.get('total_predictions', 0)}")
            print(f"   Average Accuracy: {data.get('average_accuracy', 0)}")
            print(f"   Predictions with Actual Data: {data.get('predictions_with_actual', 0)}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
        
        self.log_test(f"/stats/accuracy?store_id={TEST_STORE_ID}", "GET", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_delete_prediction(self):
        """Test delete prediction endpoint."""
        if not self.prediction_id:
            print("\n⚠️  Skipping Delete Prediction - no prediction ID available")
            return None
            
        print(f"\n🔍 Testing Delete Prediction: {self.prediction_id}...")
        
        result = await self.make_request("DELETE", f"/predictions/{self.prediction_id}")
        
        if result["success"]:
            data = result["data"]
            print(f"   Message: {data.get('message')}")
        else:
            print(f"   Failed: {result.get('error', 'Unknown error')}")
            if result["data"]:
                print(f"   Response: {result['data']}")
        
        self.log_test(f"/predictions/{self.prediction_id}", "DELETE", result["status"], result["success"], result.get("error"))
        return result
    
    async def test_error_cases(self):
        """Test error cases and edge cases."""
        print("\n🔍 Testing Error Cases...")
        
        # Test invalid prediction ID - should return 404
        result = await self.make_request("GET", "/predictions/invalid_id")
        expected_success = result["status"] == 404  # 404 is correct for invalid ID
        self.log_test("/predictions/invalid_id", "GET", result["status"], expected_success, "Should return 404 for invalid ID")
        
        # Test invalid store ID - should return empty list
        result = await self.make_request("GET", "/predictions/store/invalid_store")
        expected_success = result["success"] and result["data"] == []  # Empty list is correct
        self.log_test("/predictions/store/invalid_store", "GET", result["status"], expected_success, "Should return empty list for invalid store")
        
        # Test invalid product ID - should return empty list
        result = await self.make_request("GET", "/predictions/product/invalid_product")
        expected_success = result["success"] and result["data"] == []  # Empty list is correct
        self.log_test("/predictions/product/invalid_product", "GET", result["status"], expected_success, "Should return empty list for invalid product")
        
        # Test invalid forecast request - should return 404 for no data
        payload = {
            "store_id": "invalid_store",
            "product_id": "invalid_product",
            "forecast_month": datetime.now().isoformat(),
            "historical_months": 12
        }
        result = await self.make_request("POST", "/predict-forecast", json=payload)
        expected_success = result["status"] == 404  # 404 is correct for no historical data
        self.log_test("/predict-forecast (invalid data)", "POST", result["status"], expected_success, "Should return 404 for no historical data")
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE API TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   {result['method']} {result['endpoint']}")
                    print(f"     Status: {result['status']}")
                    print(f"     Error: {result.get('error', 'Unknown error')}")
                    print()
        
        print(f"\n✅ SUCCESSFUL TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   {result['method']} {result['endpoint']} - {result['status']}")
        
        # Save detailed report
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests/total_tests)*100 if total_tests > 0 else 0
            },
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        with open("api_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: api_test_report.json")
        
        return successful_tests == total_tests


async def main():
    """Main test function."""
    print("🚀 Starting Comprehensive API Test Suite")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"⏱️  Timeout: {TIMEOUT}s")
    
    async with APITester() as tester:
        # Core functionality tests
        await tester.test_health_check()
        await tester.test_model_info()
        
        # Prediction tests
        await tester.test_predict_forecast()
        await tester.test_get_prediction_by_id()
        await tester.test_get_predictions_by_store()
        await tester.test_get_predictions_by_product()
        await tester.test_get_predictions_by_store_and_product()
        await tester.test_get_recent_predictions()
        
        # Management tests
        await tester.test_update_prediction()
        await tester.test_get_accuracy_stats()
        await tester.test_get_accuracy_stats_with_store()
        
        # Error cases
        await tester.test_error_cases()
        
        # Cleanup
        await tester.test_delete_prediction()
        
        # Generate report
        all_passed = tester.generate_report()
        
        if all_passed:
            print("\n🎉 All tests passed! APIs are working correctly.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the report above for details.")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1) 