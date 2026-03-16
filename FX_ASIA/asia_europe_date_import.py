import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz  # For timezone handling
import os

def load_data(file_path="/Users/gmtmaster/Documents/forex_algo/py39/MarketModels/data_collect/data/EUR_USD_M15.pkl"):
    
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

    return df

def calculate_asia_high_low(asia_data):
    
    asia_high = asia_data['ask_h'].max()  # Using ask_h for Asia High
    asia_low = asia_data['bid_l'].min()   # Using bid_l for Asia Low
    day_open = asia_data['mid_o'].iloc[0] if not asia_data.empty else np.nan
    return asia_high, asia_low, day_open

def calculate_europe_high_low(europe_data):
    
    europe_high = europe_data['ask_h'].max()  # Using ask_h for EU High
    europe_low = europe_data['bid_l'].min()   # Using bid_l for EU Low

    return europe_high, europe_low

def fetch_asia_session_data(dataset, date):
    # Define Asia session start (previous day 22:05) and end (actual day 06:00)
    asia_start = datetime(date.year, date.month, date.day, 22, 0) - timedelta(days=1)  # 22:05 previous day
    asia_end = datetime(date.year, date.month, date.day, 6, 0)  # 06:00 actual day
    day_open = datetime(date.year, date.month, date.day, 22, 0) - timedelta(days=1)
    
    # Localize these datetime objects to UTC if they are naive
    if asia_start.tzinfo is None:
        asia_start = pytz.utc.localize(asia_start)
    if asia_end.tzinfo is None:
        asia_end = pytz.utc.localize(asia_end)
    if day_open.tzinfo is None:
        day_open = pytz.utc.localize(day_open)
    
    # Fetch the data for the full Asia session
    asia_data = dataset[(dataset.index >= asia_start) & (dataset.index <= asia_end)]
    
    # Debugging: Print the selected Asia session data
    #print("Asia session data within the time range:")
    #print(asia_data)
    
    # If no data, return NaN
    if asia_data.empty:
        #print(f"No data found for Asia session {asia_start} to {asia_end}")
        return None, None, None, None
    
    asia_high, asia_low, day_open = calculate_asia_high_low(asia_data)
    
    return asia_data, asia_high, asia_low, day_open

def fetch_european_session_data(dataset, date):
    # Define EU session start (actual day day 06:00) and end (actual day 12:00)
    europe_start = datetime(date.year, date.month, date.day, 6, 0)   # 06:00 previous day
    europe_end = datetime(date.year, date.month, date.day, 12, 0)  # 12:00 actual day
    
    
    # Localize these datetime objects to UTC if they are naive
    if europe_start.tzinfo is None:
        europe_start = pytz.utc.localize(europe_start)
    if europe_end.tzinfo is None:
        europe_end = pytz.utc.localize(europe_end)
    
    
    # Fetch the data for the full Asia session
    europe_data = dataset[(dataset.index >= europe_start) & (dataset.index <= europe_end)]
    
    # Debugging: Print the selected Asia session data
    #print("Asia session data within the time range:")
    #print(asia_data)

    # If no data, return NaN
    if europe_data.empty:
        #print(f"No data found for Asia session {asia_start} to {asia_end}")
        return None, None, None
    
    europe_high, europe_low = calculate_europe_high_low(europe_data)
    
    return europe_data, europe_high, europe_low

def process_asia_sessions(df, start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        asia_data, asia_high, asia_low, day_open = fetch_asia_session_data(df, current_date)

        if asia_data is not None:
            print(f"Date: {current_date.strftime('%Y-%m-%d')} | Asia High: {asia_high}, Asia Low: {asia_low}, Day Open: {day_open}")
        else:
            print(f"Date: {current_date.strftime('%Y-%m-%d')} | No data available for the specified Asia session.")
        
        # Move to the next date
        current_date += timedelta(days=1)

def process_europe_sessions(df, start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        europe_data, europe_high, europe_low = fetch_european_session_data(df, current_date)

        if europe_data is not None:
            print(f"Date: {current_date.strftime('%Y-%m-%d')} | Europe High: {europe_high}, Europe Low: {europe_low}")
        else:
            print(f"Date: {current_date.strftime('%Y-%m-%d')} | No data available for the specified EU session.")
        
        # Move to the next date
        current_date += timedelta(days=1)

if __name__ == "__main__":
    df = load_data()
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 3, 24)
    process_asia_sessions(df, start_date, end_date)
    process_europe_sessions(df, start_date, end_date)