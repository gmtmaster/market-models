import pandas as pd

data = {
    "day": ["Mon", "Mon", "Tue", "Tue", "Wed", "Wed", "Thu", "Fri"],
    "session": ["London", "NY", "Asia", "London", "NY", "London", "Asia", "NY"],
    "result": [25, -10, 15, 30, -5, 20, -8, 40]
}

df = pd.DataFrame(data)

london_mean = df[df["session"] == "London"]["result"].mean()

winning_trade = df[df["result"] > 0]

best_trade = df["result"].idxmax()

print(london_mean)
print(len(winning_trade))
print(df.loc[best_trade])