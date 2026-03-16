import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score

# Define parameters
granularity = '15T'  # 15-minute frequency
days = 10
initial_open_price = 1.1000
periods_per_day = 24 * 4  # 24 hours * 4 periods (15 min)

# Generate date range for 10 days with 15-minute intervals
date_range = pd.date_range(start="2025-03-17 00:00", periods=days * periods_per_day, freq=granularity)

# Initialize the OHLC data with the first open price
np.random.seed(42)
open_prices = np.full(len(date_range), initial_open_price)

# Generate random price variations for High, Low, Close, keeping in mind typical market behavior
high_prices = open_prices + np.random.normal(0.0001, 0.001, len(date_range))  # High > Open
low_prices = open_prices - np.random.normal(0.0001, 0.001, len(date_range))   # Low < Open
close_prices = open_prices + np.random.normal(0.0001, 0.0005, len(date_range))  # Close near Open

# Ensure high > low and close is between open and high/low
high_prices = np.maximum(high_prices, low_prices + 0.00005)
close_prices = np.clip(close_prices, low_prices, high_prices)

# Create the DataFrame with Open, High, Low, Close prices
ohlc_data = pd.DataFrame({
    'Date': date_range,
    'Open': open_prices,
    'High': high_prices,
    'Low': low_prices,
    'Close': close_prices
})

# Randomize Day Open (ODay) by adding small random fluctuations around a starting point
randomized_open_prices = initial_open_price + np.random.normal(0.0001, 0.001, days)

# Define Asia session time frame (00:00 to 06:00 UTC)
asia_start = '00:00:00'
asia_end = '06:00:00'

# Extract Asia session data for each day (from 00:00 to 06:00)
ohlc_data['Date'] = pd.to_datetime(ohlc_data['Date'])
ohlc_data['Date_only'] = ohlc_data['Date'].dt.date
asia_session = ohlc_data[(ohlc_data['Date'].dt.strftime('%H:%M:%S') >= asia_start) & 
                         (ohlc_data['Date'].dt.strftime('%H:%M:%S') <= asia_end)]

# Calculate Asia High, Asia Low, and Asia Mid for each day
data = asia_session.groupby('Date_only').agg(
    HAsia=('High', 'max'),
    LAsia=('Low', 'min')
)

# Calculate Asia Mid as the average of Asia High and Asia Low
data['MAsia'] = (data['HAsia'] + data['LAsia']) / 2

# Assign randomized Day Open (ODay) to each day
data['ODay'] = randomized_open_prices

# Show the result
print(data)


data['Y'] = 1
threshold = 0
# Now you can print the result
for index, row in data.iterrows():
    if row['ODay'] - row['MAsia'] > threshold:
        row['Y'] = 1
        print(f"Y = 1 probability increased at index {index}")
    else:
        row['Y'] = 0
        print(f"Y = 0 probability increased at index {index}")

data['True_Y'] = np.where(data['HAsia'] > data['ODay'], 1, 0)



cm = confusion_matrix(data['True_Y'], data['Y'])
accuracy = accuracy_score(data['True_Y'], data['Y'])



print("Confusion Matrix:")
print(cm)
print(f"Accuracy: {accuracy * 100:.2f}%")