# Postman Collection Setup Guide

## 📁 Files Created
- `Replenishment_Service_API.postman_collection.json` - Complete Postman collection

## 🚀 How to Import

### Method 1: Import File
1. Open **Postman**
2. Click **"Import"** (top left)
3. Click **"Upload Files"**
4. Select `Replenishment_Service_API.postman_collection.json`
5. Click **"Import"**

### Method 2: Copy/Paste
1. Open **Postman**
2. Click **"Import"** (top left)
3. Click **"Raw text"** tab
4. Copy the contents of `Replenishment_Service_API.postman_collection.json`
5. Paste and click **"Import"**

## ⚙️ Collection Variables

The collection comes with these pre-configured variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `{{base_url}}` | `http://localhost:8000/api/v1` | Base URL for all API calls |
| `{{store_id}}` | `20000` | Default store ID |
| `{{product_id}}` | `ASC1SALBC00347` | Default product ID |
| `{{prediction_id}}` | (empty) | Will be set after creating predictions |

## 📋 API Endpoints Included

### Health & Status
- **Health Check** - `GET /health`
- **Get Model Info** - `GET /model/info`

### Predictions
- **Generate Forecast** - `POST /predict-forecast`
- **Get Prediction by ID** - `GET /predictions/{id}`
- **Get Predictions by Store** - `GET /predictions/store/{store_id}`
- **Get Predictions by Product** - `GET /predictions/product/{product_id}`
- **Get Predictions by Store & Product** - `GET /predictions/store/{store_id}/product/{product_id}`
- **Get Recent Predictions** - `GET /predictions/recent`

### Prediction Management
- **Update Prediction** - `PUT /predictions/{id}`
- **Delete Prediction** - `DELETE /predictions/{id}`

### Analytics
- **Get Accuracy Statistics** - `GET /stats/accuracy`

## 🔄 Workflow Example

1. **Start with Health Check** - Verify service is running
2. **Check Model Info** - See model status and metrics
3. **Generate Forecast** - Create a new prediction
4. **Copy Prediction ID** - From the response
5. **Set Variable** - Update `{{prediction_id}}` in collection variables
6. **Get Prediction** - Retrieve the created prediction
7. **Update with Actual Data** - When real sales data is available

## 💡 Tips

### Setting Prediction ID Automatically
Add this to the **Tests** tab of "Generate Forecast":

```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.collectionVariables.set("prediction_id", response.prediction_id);
}
```

### Dynamic Dates
For the forecast request, you can use dynamic dates:
```json
{
  "forecast_month": "{{$timestamp}}"
}
```

### Environment Variables
Create a Postman environment for different configurations:
- **Development**: `http://localhost:8000/api/v1`
- **Staging**: `https://staging-api.example.com/api/v1`
- **Production**: `https://api.example.com/api/v1`

## 🎯 Quick Start

1. **Import the collection**
2. **Ensure your service is running** (`python main.py`)
3. **Run "Health Check"** to verify connection
4. **Run "Generate Forecast"** to create your first prediction
5. **Explore other endpoints** as needed

## 📊 Expected Responses

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-07-23T05:41:20.474588",
  "version": "1.0.0",
  "database_connected": true,
  "model_loaded": true
}
```

### Forecast Response
```json
{
  "prediction_id": "68807600f17a14bc1dac0cf1",
  "store_id": "20000",
  "product_id": "ASC1SALBC00347",
  "forecast_month": "2025-08-01T00:00:00",
  "predicted_quantity": 5,
  "confidence_score": 0.8145062499999999,
  "model_version": "v20250723_110125",
  "created_at": "2025-07-23T05:41:20.474588"
}
```

Happy testing! 🚀 