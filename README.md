# Replenishment Service

AI-powered replenishment forecasting service using XGBoost for retail inventory management.

## Features

- **XGBoost-based Forecasting**: Advanced machine learning model for accurate sales predictions
- **RESTful API**: Complete CRUD operations for predictions and model management
- **MongoDB Integration**: Scalable data storage for predictions and model metadata
- **Node.js Integration**: Seamless connection with existing Node.js ERP systems
- **Real-time Predictions**: Fast, accurate forecasting with confidence scores
- **Model Management**: Version control, retraining, and performance monitoring
- **Production Ready**: Logging, error handling, and health checks

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Node.js API   │    │  Replenishment   │    │    MongoDB      │
│   (Sales Data)  │◄──►│     Service      │◄──►│   (Predictions) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   XGBoost Model  │
                       │   (Forecasting)  │
                       └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.8+
- MongoDB
- Node.js API (for sales data)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd replenishment_service
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start the service**
   ```bash
   python main.py
   ```

The service will be available at `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=replenishment_service
MONGODB_COLLECTION=predictions

# Node.js API Configuration
NODEJS_API_BASE_URL=http://localhost:3000/api
NODEJS_API_KEY=your_nodejs_api_key_here

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Model Configuration
MODEL_PATH=./models/xgboost_model.pkl
MODEL_RETRAIN_INTERVAL_DAYS=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/replenishment_service.log

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Feature Engineering
HISTORICAL_MONTHS=12
FORECAST_HORIZON=3
```

## API Endpoints

### Health Check
```http
GET /api/v1/health
```

### Generate Forecast
```http
POST /api/v1/predict-forecast
Content-Type: application/json

{
  "store_id": "store_001",
  "product_id": "product_001",
  "forecast_month": "2024-02-01T00:00:00",
  "historical_months": 12
}
```

### Get Prediction
```http
GET /api/v1/predictions/{prediction_id}
```

### Get Predictions by Store
```http
GET /api/v1/predictions/store/{store_id}?limit=100
```

### Get Predictions by Product
```http
GET /api/v1/predictions/product/{product_id}?limit=100
```

### Update Prediction
```http
PUT /api/v1/predictions/{prediction_id}
Content-Type: application/json

{
  "actual_quantity": 150,
  "accuracy": 0.85
}
```

### Delete Prediction
```http
DELETE /api/v1/predictions/{prediction_id}
```

### Get Accuracy Statistics
```http
GET /api/v1/stats/accuracy?store_id=store_001
```

### Get Model Information
```http
GET /api/v1/model/info
```

## Model Training

### Initial Training
```bash
python scripts/train_model.py
```

### Retraining
The model can be retrained periodically using the same script or through the API.

## Testing

### Run API Tests
```bash
python scripts/test_api.py
```

### Manual Testing
1. Start the service: `python main.py`
2. Open browser: `http://localhost:8000/docs`
3. Use the interactive API documentation

## Integration with Node.js

### From Node.js to Python Service
```javascript
const axios = require('axios');

// Generate forecast
const response = await axios.post('http://localhost:8000/api/v1/predict-forecast', {
  store_id: 'store_001',
  product_id: 'product_001',
  forecast_month: new Date().toISOString(),
  historical_months: 12
});

console.log('Predicted quantity:', response.data.predicted_quantity);
```

### Node.js API Requirements
Your Node.js API should provide these endpoints:

```javascript
// GET /api/sales
// Query params: store_id, product_id, start_date, end_date
// Returns: { sales: [...] }

// GET /api/stores/{store_id}/products
// Returns: { products: [...] }
```

## Project Structure

```
replenishment_service/
├── app/
│   ├── api/
│   │   └── routes.py          # FastAPI routes
│   ├── config.py              # Configuration settings
│   ├── database/
│   │   └── connection.py      # MongoDB connection
│   ├── main.py                # FastAPI application
│   ├── models/
│   │   └── schemas.py         # Pydantic schemas
│   ├── repositories/
│   │   └── prediction_repository.py  # Database operations
│   └── services/
│       ├── data_service.py    # Data fetching and processing
│       └── ml_service.py      # ML model operations
├── scripts/
│   ├── train_model.py         # Model training script
│   └── test_api.py            # API testing script
├── models/                    # Saved ML models
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
├── env.example               # Environment variables template
├── main.py                   # Application entry point
└── README.md                 # This file
```

## Development

### Code Style
- Follow PEP 8
- Use type hints
- Keep functions under 50 lines
- Keep files under 500 lines
- Add docstrings for all functions

### Adding New Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
1. Set `DEBUG=False`
2. Configure production MongoDB
3. Set secure `SECRET_KEY`
4. Configure proper CORS origins
5. Setup monitoring and logging

## Monitoring

### Health Checks
- Service health: `GET /api/v1/health`
- Database connectivity
- Model availability

### Logs
- Application logs: `./logs/replenishment_service.log`
- Log rotation: 10MB files, 30 days retention

### Metrics
- Prediction accuracy
- API response times
- Model performance

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check MongoDB is running
   - Verify connection string in `.env`

2. **Model Not Found**
   - Run `python scripts/train_model.py`
   - Check model path in configuration

3. **Node.js API Unreachable**
   - Verify API URL in `.env`
   - Check network connectivity
   - Validate API key

4. **Prediction Errors**
   - Ensure sufficient historical data
   - Check feature engineering pipeline
   - Verify model is trained

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

[Your License Here]

## Support

For support and questions:
- Create an issue
- Check documentation
- Review logs
