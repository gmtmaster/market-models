import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz  # For timezone handling
import os

# Load data
current_directory = os.getcwd()
file_path = os.path.join(current_directory, 'data_collect', 'data', 'EUR_USD_M15.pkl')

df = pd.read_pickle(file_path)

# Ensure 'time' is in datetime format
df['time'] = pd.to_datetime(df['time'])

# Set 'time' as the index to work with datetime operations
df.set_index('time', inplace=True)

# Ensure the time zone is UTC (if it's not already)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')  # Ensure it's in UTC if already tz-aware

def fetch_asia_session_data(dataset, date):
    # Define Asia session start (previous day 22:05) and end (actual day 06:00)
    asia_start = datetime(date.year, date.month, date.day, 22, 5) - timedelta(days=1)  # 22:05 previous day
    asia_end = datetime(date.year, date.month, date.day, 6, 0)  # 06:00 actual day
    
    # Localize these datetime objects to UTC if they are naive
    if asia_start.tzinfo is None:
        asia_start = pytz.utc.localize(asia_start)
    if asia_end.tzinfo is None:
        asia_end = pytz.utc.localize(asia_end)
    
    # Fetch the data for the full Asia session
    asia_data = dataset[(dataset.index >= asia_start) & (dataset.index <= asia_end)]
    
    # Debugging: Print the selected Asia session data
    print("Asia session data within the time range:")
    print(asia_data)
    
    # If no data, return NaN
    if asia_data.empty:
        print(f"No data found for Asia session {asia_start} to {asia_end}")
        return None, None, None
    
    # Calculate Asia High and Low
    asia_high = asia_data['ask_h'].max()  # Using ask_h for Asia High
    asia_low = asia_data['bid_l'].min()   # Using bid_l for Asia Low
    
    return asia_data, asia_high, asia_low

# Example usage: Loop through a range of dates
start_date = datetime(2025, 3, 1)  # Start date
end_date = datetime(2025, 3, 14)    # End date

current_date = start_date
while current_date <= end_date:
    asia_data, asia_high, asia_low = fetch_asia_session_data(df, current_date)

    if asia_data is not None:
        print(f"Date: {current_date.strftime('%Y-%m-%d')} | Asia High: {asia_high}, Asia Low: {asia_low}")
    else:
        print(f"Date: {current_date.strftime('%Y-%m-%d')} | No data available for the specified Asia session.")
    
    # Move to the next date
    current_date += timedelta(days=1)
