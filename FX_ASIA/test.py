import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score
from asia_europe_date_import import load_data, fetch_asia_session_data, fetch_european_session_data
from datetime import datetime

df = load_data()
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 3, 24)

# Initialize lists to store the calculated data
dates = []
asia_highs = []
asia_lows = []
day_opens = []
european_highs = []
european_lows = []
breakout_orders = []
predicts = []

# Loop through the dates and fetch the session datas
current_date = start_date
while current_date <= end_date:
    asia_data, asia_high, asia_low, day_open = fetch_asia_session_data(df, current_date)
    european_data, european_high, european_low = fetch_european_session_data(df, current_date)

    if asia_data is not None and not asia_data.empty and european_data is not None and not european_data.empty:
        dates.append(current_date)
        asia_highs.append(asia_high)
        asia_lows.append(asia_low)
        day_opens.append(day_open)
        european_highs.append(european_high)
        european_lows.append(european_low)

        breakout = 0
        for _, row in european_data.iterrows():
            if row['ask_h'] > asia_high:
                breakout = "1"
                break
            elif row['bid_l'] < asia_low:
                breakout = "0"
                break

        breakout_orders.append(breakout)
        predicts.append(1 if breakout == "1" else 0)

    else:
        dates.append(current_date)
        asia_highs.append(None)
        asia_lows.append(None)
        day_opens.append(None)
        european_highs.append(None)
        european_lows.append(None)
        breakout_orders.append(None)
        predicts.append(None)

    # Move to the next day
    current_date += pd.Timedelta(days=1)

# Create the final DataFrame
data = pd.DataFrame({
    'Date': dates,
    'HAsia': asia_highs,
    'LAsia': asia_lows,
    'ODay': day_opens,
    'HEu': european_highs,
    'LEu': european_lows,
    'True_Y': breakout_orders,
    'Y': predicts
    })

data.dropna(inplace=True)

#Rule 1
#Conditions
data['MAsia'] = (data['HAsia'] + data['LAsia']) / 2
data['RAsia'] = data['HAsia'] - data['LAsia']
data['True_Y'] = data['True_Y'].fillna(0).astype(int)
data['Y'] = data['Y'].astype(int)

data['Y'] = 1
threshold = 0

data['Y'] = np.where(data['ODay'] - data['MAsia'] > threshold, 1, 0)

print(data)

#na most elméletileg a Y_True értékek jók és mindig pontosak.
#rule1 elméletiekben megfelel a kondicionak, viszont nagyon alacsony
#36% a pontosság. ezzel kell valamit csinálni. kicsit újra értelmezni
#átfogalmazni stbstb. ha ez a modell elérne egy 50-70% közti értéket
#akkor mehetnénk a következő szabályra.


cm = confusion_matrix(data['True_Y'], data['Y'])
accuracy = accuracy_score(data['True_Y'], data['Y'])



print("Confusion Matrix:")
print(cm)
print(f"Accuracy: {accuracy * 100:.2f}%")