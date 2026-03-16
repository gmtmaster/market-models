import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score

# Define column names for the dataset
column_names = ['datetime', 'Open', 'High', 'Low', 'Close', 'Volume']

# Load the CSV file (tab-separated format)
data = pd.read_csv('EURUSD15.csv', sep='\t', names=column_names, header=None, parse_dates=['datetime'])

# Convert 'datetime' column to proper datetime format and set it as index
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# Ensure the data is sorted by time
data.sort_index(inplace=True)

# -----------------------------
# Extract Asia Session Metrics
# -----------------------------

# Create a 'TradingDay' column where Asia session (00:00-05:00 UTC) belongs to the previous day
data['TradingDay'] = pd.to_datetime(data.index.date)
data.loc[data.index.hour < 5, 'TradingDay'] -= pd.Timedelta(days=1)

# Filter Asia session data (21:00-05:00 UTC)
asia_session_data = data.between_time('21:00', '23:59').copy()
asia_session_data = pd.concat([asia_session_data, data.between_time('00:00', '05:00')])

# Calculate Asia session metrics per trading day
asia_summary = asia_session_data.groupby('TradingDay').agg(
    Asia_High=('High', 'max'),
    Asia_Low=('Low', 'min'),
    Asia_Mid=('Low', 'min'),  # Placeholder, will update next
    Day_Open=('Open', 'first')
).reset_index()

# Compute Asia Mid (corrected formula)
asia_summary['Asia_Mid'] = (asia_summary['Asia_High'] + asia_summary['Asia_Low']) / 2

# -----------------------------
# Determine European Session Breaches
# -----------------------------

# Define European session time range (Frankfurt: 06:00-11:00 UTC)
europe_start = '06:00'
europe_end = '11:00'

# List to store results
european_session_results = []

# Loop through each trading day
for _, row in asia_summary.iterrows():
    trading_day = row['TradingDay']
    HAsia = row['Asia_High']
    LAsia = row['Asia_Low']
    
    # Extract European session data
    europe_session = data.loc[data.index.normalize() == trading_day].between_time(europe_start, europe_end)


    if not europe_session.empty:
        # Find first timestamp breaching HAsia
        breach_high = europe_session[europe_session['High'] > HAsia]
        first_high_time = breach_high.index.min() if not breach_high.empty else None

        # Find first timestamp breaching LAsia
        breach_low = europe_session[europe_session['Low'] < LAsia]
        first_low_time = breach_low.index.min() if not breach_low.empty else None

        # Determine Y (1 if HAsia breached first, 0 if LAsia breached first)
        if first_high_time and first_low_time:
            Y = 1 if first_high_time < first_low_time else 0
        elif first_high_time:
            Y = 1
        elif first_low_time:
            Y = 0
        else:
            Y = None  # No breach occurred

        # Store results
        european_session_results.append({
            'TradingDay': trading_day,
            'Asia_High': HAsia,
            'Asia_Low': LAsia,
            'First_High_Breach': first_high_time,
            'First_Low_Breach': first_low_time,
            'Y': Y
        })

# Convert to DataFrame
europe_df = pd.DataFrame(european_session_results)

# Merge the European session results with Asia session data
final_df = pd.merge(asia_summary, europe_df, on='TradingDay', how='left')

# Display the final structured dataset
print(final_df.head())

# Rename the columns to ensure consistency
final_df.rename(columns={'Asia_High_x': 'Asia_High', 'Asia_Low_x': 'Asia_Low'}, inplace=True)


# Step 1: Calculate Asia session price range (Asia_Range)
final_df['Asia_Range'] = final_df['Asia_High'] - final_df['Asia_Low']

# Step 2: Calculate the median of Asia_Range
median_asia_range = final_df['Asia_Range'].median()

# Step 3: Apply the composite rule
final_df['Composite_Prediction'] = np.where(
    (final_df['Day_Open'] > final_df['Asia_Mid']) & (final_df['Asia_Range'] > median_asia_range), 
    1, 
    0
)

# Step 4: Drop rows where either 'Y' or 'Composite_Prediction' is NaN
valid_data = final_df.dropna(subset=['Y', 'Composite_Prediction'])

# Check for NaNs in 'Y' and 'Composite_Prediction'
if valid_data['Y'].isnull().any() or valid_data['Composite_Prediction'].isnull().any():
    print("There are still NaN values in the data!")
else:
    # Evaluate the composite rule using confusion matrix and accuracy score
    y_true = valid_data['Y']  # Ground truth (actual Y values)
    y_pred = valid_data['Composite_Prediction']  # Predicted Y values from the composite rule

    # Confusion matrix
    conf_matrix = confusion_matrix(y_true, y_pred)

    # Accuracy score
    accuracy = accuracy_score(y_true, y_pred)

    # Output the results
    print(f"Confusion Matrix:\n{conf_matrix}")
    print(f"Accuracy of Composite Rule-Based Model: {accuracy * 100:.2f}%")

# Check the number of unique trading days
unique_trading_days = final_df['TradingDay'].nunique()
print(f"Number of unique trading days in the dataset: {unique_trading_days}")