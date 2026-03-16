import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score
import matplotlib.pyplot as plt

# Step 1: Prepare your dataset
# For this example, we will create mock data for 1000 trading days
np.random.seed(42)

# Example data generation (Replace with actual data fetching logic)
data = pd.DataFrame({
    'Date': pd.date_range(start='2025-01-01', periods=1000, freq='B'),
    'Asia_High': np.random.uniform(1.1000, 1.1500, 1000),  # Simulating Asia High
    'Asia_Low': np.random.uniform(1.0500, 1.1000, 1000),   # Simulating Asia Low
    'Day_Open': np.random.uniform(1.0800, 1.1100, 1000),   # Simulating Day Open
})

# Step 2: Feature Extraction
# Calculate MAsia (Midpoint of Asia session range)
data['Asia_Mid'] = (data['Asia_High'] + data['Asia_Low']) / 2
data['Asia_Range'] = data['Asia_High'] - data['Asia_Low']  # Range of Asia session

# Step 3: Define rules for prediction (based on Day Open, Asia Mid, and Asia Range)
# Rule 1: If Day Open > Asia Mid, predict price will breach Asia High
data['Predict_High'] = (data['Day_Open'] > data['Asia_Mid']).astype(int)

# Rule 2: Combine Rule 1 with momentum (Asia range greater than median)
median_range = data['Asia_Range'].median()
data['Predict_High'] = ((data['Day_Open'] > data['Asia_Mid']) & (data['Asia_Range'] > median_range)).astype(int)

# Composite Rule: Combine multiple factors (Day Open > Asia Mid, and Asia Range larger than median)
data['Composite_Predict'] = ((data['Day_Open'] > data['Asia_Mid']) & 
                              (data['Asia_Range'] > median_range)).astype(int)

# Step 4: Generate actual outcomes (for backtesting purposes, replace this with actual trading results)
# Assume that the price actually breaches Asia High if the Day Open is greater than Asia Mid
data['Actual'] = (data['Day_Open'] > data['Asia_Mid']).astype(int)  # Replace with actual outcome logic

# Step 5: Model Evaluation using confusion matrix and accuracy
cm = confusion_matrix(data['Actual'], data['Composite_Predict'])
accuracy = accuracy_score(data['Actual'], data['Composite_Predict'])

# Display confusion matrix and accuracy
print("Confusion Matrix:\n", cm)
print(f"Accuracy: {accuracy:.2f}")


# Optional: Backtesting - simulate the actual trading strategy (this could be extended further)
# Here, we'll simulate a simple strategy of executing buy when predicted correctly
initial_balance = 10000  # Starting balance in USD
balance = initial_balance
for index, row in data.iterrows():
    if row['Composite_Predict'] == row['Actual']:  # Correct prediction
        # If prediction is correct, simulate a gain (for simplicity, 0.1% profit on each trade)
        balance *= 1.001  # 0.1% return for correct prediction
    else:
        # If prediction is wrong, simulate a loss (for simplicity, 0.1% loss on each trade)
        balance *= 0.999  # 0.1% loss for incorrect prediction

# Final balance after backtesting
print(f"Final Balance after Backtesting: ${balance:.2f}")

