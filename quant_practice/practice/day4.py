import pandas as pd

data = {
    "day": ["Mon", "Mon", "Tue", "Tue", "Wed", "Wed", "Thu", "Fri"],
    "session": ["London", "NY", "Asia", "London", "NY", "London", "Asia", "NY"],
    "result": [25, -10, 15, 30, -5, 20, -8, 40]
}

df = pd.DataFrame(data)

df["status"] = df["result"].apply(lambda x: "Win" if x > 0 else "Loss")

df["strength"] = df["result"].apply(lambda x: "Strong" if x >= 20 else "Weak")

df["score"] = df.apply( 
    lambda row: "A" if row["status"] == "Win" and row["strength"] == "Strong" 
    else "B" if row["status"] == "Win" and row["strength"] == "Weak" 
    else "C", 
    axis=1 )

df["priority"] = df.apply(
    lambda row: "High" if row["session"] == "London" and row["score"] == "A"
    else "Medium" if row["session"] == "NY" and row["score"] == "A"
    else "Low",
    axis=1
)

df["trade_type"] = df.apply(
    lambda row: "Momentum" if row["status"] == "Win" and row["session"] == "London"
    else "Normal Win" if row["status"] == "Win" and row["session"] != "London"
    else "Loss Trade",
    axis=1
)


print(df)