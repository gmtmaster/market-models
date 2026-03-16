import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score
import matplotlib.pyplot as plt

# Load your real dataset
df = pd.read_pickle("/Users/gmtmaster/Documents/forex_algo/py39/MarketModels/data_collect/data/EUR_USD_M15.pkl")  # Replace with actual file path

# Ensure time is in datetime format and set index
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

# Print all the 15-minute timestamps to verify
print("Processed 15-minute timestamps:")
print(df.index)

# Create empty lists to store calculated features
asia_high_list = []
asia_low_list = []
day_open_list = []

# Iterate over each day to calculate Asia session high, low, and Day Open
for date in df.resample('D').max().index:
    print(f"Processing date: {date}")
    
    # Filter the data for the Asia session from 22:05 on the previous day to 06:00 on the current day
    asia_session = df.loc[date - pd.Timedelta(days=1):date].between_time("22:05", "06:00")
    
    # Debugging: Print the first few rows of the Asia session
    print(f"Asia session for {date}:")
    print(asia_session.head())
    
    # Check if the Asia session is not empty
    if not asia_session.empty:
        # Calculate Asia High and Low from the Asia session
        asia_high = asia_session['ask_h'].max()  # Max of ask_h during Asia session
        asia_low = asia_session['bid_l'].min()   # Min of bid_l during Asia session
        
        # Calculate Day Open from the first mid_o between 22:05 and 22:15
        day_open = asia_session['mid_o'].iloc[0]  # First mid_o value during 22:05-22:15 for Day Open
        
        # Debugging: Print calculated values
        print(f"Asia High: {asia_high}, Asia Low: {asia_low}, Day Open: {day_open}")
        
        # Append the results to the lists
        asia_high_list.append(asia_high)
        asia_low_list.append(asia_low)
        day_open_list.append(day_open)
    else:
        asia_high_list.append(np.nan)
        asia_low_list.append(np.nan)
        day_open_list.append(np.nan)

# Create a new dataframe with the extracted features for each day
data = pd.DataFrame({
    'Date': df.resample('D').max().index,  # Daily timestamps
    'Asia_High': asia_high_list,
    'Asia_Low': asia_low_list,
    'Day_Open': day_open_list,
})

# Check for rows with NaN values
print(f"Rows with NaN values: {data[data.isna().any(axis=1)]}")

# Drop rows with NaN values (if any)
data.dropna(inplace=True)

# Compute Midpoint and Range of Asia Session
data['Asia_Mid'] = (data['Asia_High'] + data['Asia_Low']) / 2
data['Asia_Range'] = data['Asia_High'] - data['Asia_Low']

# Debugging: Check if calculations look correct
print(data[['Date', 'Asia_High', 'Asia_Low', 'Day_Open', 'Asia_Mid', 'Asia_Range']].head())

# Define trading rules
data['Predict_High'] = (data['Day_Open'] > data['Asia_Mid']).astype(int)
median_range = data['Asia_Range'].median()
data['Composite_Predict'] = ((data['Day_Open'] > data['Asia_Mid']) & 
                              (data['Asia_Range'] > median_range)).astype(int)

# Simulated actual outcomes (replace with real results if available)
data['Actual'] = (data['Day_Open'] > data['Asia_Mid']).astype(int)  # Placeholder logic

# Evaluate Model Performance
cm = confusion_matrix(data['Actual'], data['Composite_Predict'])
accuracy = accuracy_score(data['Actual'], data['Composite_Predict'])

print("Confusion Matrix:\n", cm)
print(f"Accuracy: {accuracy:.2f}")

# Debugging: Check unique values and final balance
print("Unique values in Actual:", data['Actual'].unique())
print("Unique values in Composite_Predict:", data['Composite_Predict'].unique())

# Backtesting
initial_balance = 10000
balance = initial_balance
for _, row in data.iterrows():
    if row['Composite_Predict'] == row['Actual']:
        balance *= 1.001  # 0.1% gain
    else:
        balance *= 0.999  # 0.1% loss

print(f"Final Balance after Backtesting: ${balance:.2f}")
