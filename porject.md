 PHASE 2: Machine Learning Forecasting (XGBoost-based) 
Goal: Improve forecast accuracy by training a model on historical sales data using XGBoost — 
a powerful, beginner-friendly algorithm. 
�
�
 Step 1: What is XGBoost (in simple words)? 
● XGBoost is a smart calculator that learns patterns from your old sales. 
● It considers multiple things like month, store, product, trends, and seasonality. 
● After learning, it can predict future sales more accurately than just averaging. 
�
�
 Step 2: Prepare Your Data (called Feature Engineering) 
For each record, create columns like: 
● store 
● product 
● month / year 
● sales_last_1_month 
● sales_last_2_months 
● sales_last_3_months 
● average_discount 
● is_festival_month (1 or 0) 
● forecast_qty (this is the target label XGBoost learns from) 
Use Pandas (Python) to prepare this data. 
�
�
 Step 3: Train the XGBoost Model 
What you’ll do: 
● Split your dataset: 80% for training, 20% for testing 
● Use XGBoost Regressor from xgboost Python library 
● Feed the historical rows with known sales to train the model 
● Evaluate it using MAE or MAPE to measure how close it is to real sales 
�
�
 Step 4: Deploy Model as a Microservice 
Why? So your Node.js ERP can call it like an API 
What to do: 
● Create a simple Python server using FastAPI or Flask 
● Add a route /predict-forecast which: 
○ Takes product + store + month data as input 
○ Returns predicted quantity for the next month 
You can run this Python service on the same server or use a Docker container. 
�
�
 Step 5: Connect from Node.js 
From your ERP system: 
● Use Axios/Fetch to send product-store-month data to your Python endpoint 
● Receive forecast and show it on the dashboard 
● Save it in DB for comparison later 
�
�
 Tooling You’ll Need for Phase 2 
Task 
Data Prep 
Model Training 
Tools 
Pandas, Numpy 
XGBoost, Scikit-learn 
Model Serving 
Call from ERP 
Store/Query Data 
Flask or FastAPI (Python) 
Axios/Fetch in Node.js 
MongoDB/PostgreSQL 
Let me know when you’re ready to: 
● See a sample training dataset format 
● Set up the Python XGBoost project 
● Get sample code for prediction API 
Once Phase 2 is working, we’ll move to Phase 3 (model improvement using real sales 
feedback). 
�
�



 PHASE 3: Feedback Loop & Accuracy Tuning 
Goal: Continuously improve the model using real sales data 
�
�
 Step 1: Compare Forecast vs Actuals 
Each month: 
● accuracy = 1 - abs(forecast - actual) / actual 
● Track MAPE (Mean Absolute Percentage Error) 
�
�
 Step 2: Retrain Model Regularly 
● Store new actual data 
● Add to training set 
● Retrain model monthly or quarterly 
�
�
 Step 3: Show Insights in Dashboard 
● Forecast vs Actual chart 
● Accuracy per product/store 
● Auto-alert for underperforming SKUs 
�
�
 Tooling & Stack 
Task 
Data Handling 
Tool/Stack 
Pandas (Python) 
Basic Forecasting JS/Node or Pandas 
ML Models Scikit-learn, XGBoost 
Microservice Python + FastAPI or Flask 
Integration Axios/Fetch from Next.js to API 
Model Training Scheduler CRON job or Airflow 
Storage MongoDB / PostgreSQL
























#Ignore this jsut for refrence 
 How the Python Service Works with Your Node.js API
The Complete Process Flow
1. User Requests a Prediction
When someone wants to know how much inventory to order for next month, they send a request to the Python service. This request includes which store, which product, and which month they want to forecast.
2. Python Service Calculates Date Range
The Python service figures out how much historical data it needs. For example, if someone wants to predict February 2024, it will ask for sales data from February 2023 to January 2024 (12 months of history).
3. Python Service Calls Your Node.js API
The Python service then makes an HTTP request to your existing Node.js API. It's like making a phone call to your database asking for specific sales records. The request says: "Hey, give me all sales data for store_001, product_001, between these two dates."
4. Your Node.js API Responds
Your Node.js API receives this request and searches your database for the sales records. It finds all the sales data for that store and product within the requested time period. Then it packages this data and sends it back to the Python service.
5. Python Service Processes the Data
Once the Python service receives the sales data from your Node.js API, it starts cleaning and preparing the data. It creates additional features like:
What month each sale happened in
How sales compare to previous months
Average discounts given
Whether it was during a festival period
Rolling averages of sales
6. Machine Learning Model Makes Prediction
The Python service feeds this processed data into the XGBoost machine learning model. The model has been trained on similar patterns and can predict future sales based on historical trends, seasonality, and other factors.
7. Prediction is Stored and Returned
The model gives a prediction (like "150 units needed for next month") along with a confidence score. This prediction is saved in the MongoDB database for future reference and comparison. The Python service then sends this prediction back to whoever requested it.
What Your Node.js API Needs to Provide
Required Data Format
Your Node.js API must have an endpoint that can provide sales data in a specific format. Each sales record should include:
Store ID (which store the sale happened at)
Product ID (which product was sold)
Date (when the sale happened)
Quantity (how many units were sold)
Revenue (how much money was made)
Discount (if any discount was given)
Festival flag (whether it was during a special period)
API Endpoint Requirements
Your Node.js API needs to have a specific endpoint (like /api/sales) that can accept parameters for store ID, product ID, start date, and end date. When called, it should return all sales records that match these criteria.
Data Quality Requirements
The Python service works best when it has at least 3 months of historical data, but 12 months or more gives much better predictions. The data should be consistent and accurate, with no missing critical information.
Error Handling and Edge Cases
When Your API is Down
If your Node.js API is not responding or is down, the Python service will return an error message saying it couldn't fetch the required data. This prevents the system from making predictions based on incomplete or missing information.
When No Data Exists
If your Node.js API responds but has no sales data for the requested store and product combination, the Python service will inform the user that there's insufficient data to make a prediction.
When Data is Insufficient
If there's some data but not enough to make a reliable prediction (less than 3 months), the Python service will warn that the prediction might not be accurate.
Performance and Scalability
Request Frequency
The Python service can handle multiple prediction requests simultaneously. Each request to your Node.js API is independent, so if one request is slow, it doesn't affect others.
Data Volume
The system can handle large amounts of sales data. Even if you have thousands of sales records for a store-product combination, the Python service can process them efficiently.
Caching and Optimization
The Python service is designed to be efficient. It only requests the data it needs for each prediction, and it processes the data quickly to provide fast responses.
Integration Benefits
Seamless Connection
The Python service integrates seamlessly with your existing Node.js system. It doesn't require any changes to your current database structure or business logic. It just needs access to your sales data through the API.
Real-time Predictions
Because it connects to your live Node.js API, the Python service can provide predictions based on the most current data available. This ensures that predictions are always up-to-date with your latest sales information.
Scalable Architecture
This design allows you to scale both systems independently. You can add more stores, products, or users without affecting the prediction service, and vice versa.
Data Security
The Python service only requests the specific data it needs for each prediction. It doesn't have direct access to your entire database, maintaining security and data privacy.
This is how the Python replenishment service works as a smart assistant that asks your Node.js system for sales data, processes it with machine learning, and provides intelligent predictions for inventory management.