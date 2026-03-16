import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score

# Load Data
column_names = ['datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
data = pd.read_csv('EURUSD15.csv', sep='\t', names=column_names, header=None, parse_dates=['datetime'])
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)
data.sort_index(inplace=True)

# Define Trading Days
data['TradingDay'] = pd.to_datetime(data.index.date)
data.loc[data.index.hour < 5, 'TradingDay'] -= pd.Timedelta(days=1)

# Extract Asia Session Data (21:00-05:00 UTC)
asia_session_data = data.between_time('21:00', '23:59').copy()
asia_session_data = pd.concat([asia_session_data, data.between_time('00:00', '05:00')])

# Calculate Asia Session Metrics
asia_summary = asia_session_data.groupby('TradingDay').agg(
    Asia_High=('High', 'max'),
    Asia_Low=('Low', 'min'),
    Asia_Close=('Close', 'last'),
    Asia_Open=('Open', 'first'),
    Day_Open=('Open', 'first')
).reset_index()

asia_summary['Asia_Mid'] = (asia_summary['Asia_High'] + asia_summary['Asia_Low']) / 2
asia_summary['Asia_Range'] = asia_summary['Asia_High'] - asia_summary['Asia_Low']

# Calculate ATR (Average True Range)
asia_summary['Prev_Asia_Range'] = asia_summary['Asia_Range'].shift(1)
asia_summary['ATR'] = asia_summary['Prev_Asia_Range'].rolling(window=14).mean()

# Define European Session Time Window (06:00 - 11:00 UTC)
europe_start = '06:00'
europe_end = '11:00'
european_session_results = []

# Process Each Trading Day
for _, row in asia_summary.iterrows():
    trading_day = row['TradingDay']
    HAsia = row['Asia_High']
    LAsia = row['Asia_Low']
    
    # Extract European session data
    europe_session = data.loc[data.index.normalize() == trading_day].between_time(europe_start, europe_end)

    if not europe_session.empty:
        breach_high = europe_session[europe_session['High'] > HAsia]
        first_high_time = breach_high.index.min() if not breach_high.empty else None

        breach_low = europe_session[europe_session['Low'] < LAsia]
        first_low_time = breach_low.index.min() if not breach_low.empty else None

        if first_high_time and first_low_time:
            Y = 1 if first_high_time < first_low_time else 0
        elif first_high_time:
            Y = 1
        elif first_low_time:
            Y = 0
        else:
            Y = None

        european_session_results.append({
            'TradingDay': trading_day,
            'Asia_High': HAsia,
            'Asia_Low': LAsia,
            'First_High_Breach': first_high_time,
            'First_Low_Breach': first_low_time,
            'Y': Y
        })

# Merge European Data
europe_df = pd.DataFrame(european_session_results)
final_df = pd.merge(asia_summary, europe_df, on='TradingDay', how='left')

# DEBUG: Check column names after merging
print("Columns after merge:", final_df.columns)

# Fix column names if necessary
if 'Asia_High_x' in final_df.columns:
    final_df.rename(columns={'Asia_High_x': 'Asia_High', 'Asia_Low_x': 'Asia_Low'}, inplace=True)

# Drop Missing Values
valid_data = final_df.dropna(subset=['Y'])

# **New Composite Probability Model**
# Define a weighted probability score
final_df['Prob_Long'] = (
    0.4 * (final_df['Day_Open'] > final_df['Asia_Mid']) +
    0.3 * (final_df['Asia_Range'] > final_df['ATR']) +
    0.2 * (final_df['Asia_Close'] > final_df['Asia_Open']) +
    0.1 * (final_df['Asia_High'] > final_df['Prev_Asia_Range'])
)

# Convert probability score into binary decision
final_df['Composite_Prediction'] = (final_df['Prob_Long'] > 0.5).astype(int)

# Keep only valid rows for evaluation
valid_data = final_df.dropna(subset=['Y', 'Composite_Prediction'])

# Confusion Matrix and Accuracy Calculation
y_true = valid_data['Y']
y_pred = valid_data['Composite_Prediction']
conf_matrix = confusion_matrix(y_true, y_pred)
accuracy = accuracy_score(y_true, y_pred)

# Print Results
print(f"Confusion Matrix:\n{conf_matrix}")
print(f"Accuracy of Probability-Based Model: {accuracy * 100:.2f}%")
print(f"Number of unique trading days in the dataset: {final_df['TradingDay'].nunique()}")

# Print misclassified days for debugging
misclassified = valid_data[valid_data['Y'] != valid_data['Composite_Prediction']]
print("Misclassified Trading Days:")
print(misclassified[['TradingDay', 'Y', 'Composite_Prediction', 'Prob_Long']])
