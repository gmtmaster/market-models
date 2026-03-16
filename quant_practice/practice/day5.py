import pandas as pd

df = pd.DataFrame({
    "day": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "asia_high": [1.100, 1.102, 1.101, 1.103, 1.104],
    "europe_high": [1.101, 1.100, 1.102, 1.104, 1.103],
    "asia_low": [1.090, 1.091, 1.089, 1.092, 1.093],
    "europe_low": [1.089, 1.092, 1.088, 1.093, 1.094]
})

df["high_break"] = df.apply(
    lambda row: "held" if row["asia_high"] > row["europe_high"] else "breached",
    axis=1
)

df["low_break"] = df.apply(
    lambda row: "held" if row["asia_low"] < row["europe_low"] else "breached",
    axis=1
)

df["direction"] = df.apply(
    lambda row: "bullish" if row["high_break"] == "breached"
    else "bearish" if row["low_break"] == "breached"
    else "neutral",
    axis=1
)

filter_bullish = df["direction"] == "bullish"

print(df.loc[filter_bullish])