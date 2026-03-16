import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from sklearn.metrics import confusion_matrix, accuracy_score

# Load dataset
df = pd.read_pickle("/Users/adamleko/Desktop/forex_algo/MarketModels/data_collect/data/EUR_USD_M5.pkl")

df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

df.index = df.index.tz_localize('UTC') if df.index.tz is None else df.index.tz_convert('UTC')

def fetch_asia_session_data(dataset, date):
    asia_start = datetime(date.year, date.month, date.day, 22, 0) - timedelta(days=1)
    asia_end = datetime(date.year, date.month, date.day, 6, 0)
    
    asia_start = pytz.utc.localize(asia_start) if asia_start.tzinfo is None else asia_start
    asia_end = pytz.utc.localize(asia_end) if asia_end.tzinfo is None else asia_end
    
    asia_data = dataset[(dataset.index >= asia_start) & (dataset.index <= asia_end)]
    
    if asia_data.empty:
        return None, np.nan, np.nan, np.nan
    
    asia_high = asia_data['ask_h'].max()
    asia_low = asia_data['bid_l'].min()
    day_open = asia_data.between_time("22:00", "22:15")['mid_o'].iloc[0] if not asia_data.between_time("22:05", "22:15").empty else np.nan
    
    return asia_data, asia_high, asia_low, day_open

# Process data
start_date = df.index.date[0]
end_date = df.index.date[-1]

data_records = []
current_date = start_date

while current_date <= end_date:
    _, asia_high, asia_low, day_open = fetch_asia_session_data(df, current_date)
    if not np.isnan(asia_high) and not np.isnan(asia_low) and not np.isnan(day_open):
        data_records.append([current_date, asia_high, asia_low, day_open])
    current_date += timedelta(days=1)

# Create final dataframe
data = pd.DataFrame(data_records, columns=['Date', 'Asia_High', 'Asia_Low', 'Day_Open'])
data['Asia_Mid'] = (data['Asia_High'] + data['Asia_Low']) / 2
data['Asia_Range'] = data['Asia_High'] - data['Asia_Low']

# Define trading rules
data['Predict_High'] = (data['Day_Open'] > data['Asia_Mid']).astype(int)
median_range = data['Asia_Range'].median()
data['Composite_Predict'] = ((data['Day_Open'] > data['Asia_Mid']) & (data['Asia_Range'] > median_range)).astype(int)

data['Actual'] = (data['Day_Open'] > data['Asia_Mid']).astype(int)  # Placeholder

# Evaluate model performance
cm = confusion_matrix(data['Actual'], data['Composite_Predict'])
accuracy = accuracy_score(data['Actual'], data['Composite_Predict'])

# Generate trade signals
data['Signal'] = data['Composite_Predict'].map({1: 'LONG', 0: 'SHORT'})
data['Probability'] = accuracy  # Assign model accuracy as probability

# Print results
print("Confusion Matrix:\n", cm)
print(f"Accuracy: {accuracy:.2f}")


# Count successful predictions for LONG and SHORT signals
long_success = data[(data['Composite_Predict'] == 1) & (data['Actual'] == 1)].shape[0]
long_total = data[data['Composite_Predict'] == 1].shape[0]
short_success = data[(data['Composite_Predict'] == 0) & (data['Actual'] == 0)].shape[0]
short_total = data[data['Composite_Predict'] == 0].shape[0]

# Compute probabilities based on past outcomes
long_prob = long_success / long_total if long_total > 0 else 0.5  # Default 50% if no data
short_prob = short_success / short_total if short_total > 0 else 0.5

# Implement 77% confidence level adjustment to probabilities
confidence_level = 0.77

# Function to calculate accuracy for a rolling window
def rolling_accuracy(series):
    idx = data.index[len(series) - 1]  # Find the corresponding index
    actual_values = data.loc[idx - len(series) + 1: idx, 'Actual'].values  # Extract matching 'Actual' values
    return np.mean(series == actual_values)

# Compute rolling accuracy first
window_size = 20
data['Rolling_Accuracy'] = data['Composite_Predict'].rolling(window=window_size).apply(rolling_accuracy, raw=True)

# Now adjust the probabilities using rolling accuracy
def adjust_probability_with_confidence(prob, rolling_accuracy):
    """
    Adjusts the probability based on rolling accuracy to reflect a more confident signal.
    """
    # If rolling accuracy is above the confidence level, scale the probability up
    if rolling_accuracy >= confidence_level:
        return min(prob * 1.2, 1)  # Scale up the probability but limit it to a maximum of 1
    else:
        return prob * 0.8  # Scale down the probability if the confidence is low

# Apply this adjustment logic to each row
data['Probability'] = data.apply(
    lambda row: adjust_probability_with_confidence(long_prob, row['Rolling_Accuracy']) if row['Composite_Predict'] == 1
    else adjust_probability_with_confidence(short_prob, row['Rolling_Accuracy']), axis=1
)

# Map signals
data['Signal'] = data['Composite_Predict'].map({1: 'LONG', 0: 'SHORT'})

# Select only relevant columns
final_output = data[['Date', 'Signal', 'Probability']]
print(final_output)

# Backtesting
balance = 10000
for _, row in data.iterrows():
    balance *= 1.001 if row['Composite_Predict'] == row['Actual'] else 0.999

print(f"Final Balance after Backtesting: ${balance:.2f}")
