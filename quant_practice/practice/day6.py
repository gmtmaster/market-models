import pandas as pd

df = pd.DataFrame({
    "day": ["Mon", "Mon", "Tue", "Tue", "Wed", "Wed"],
    "session": ["London", "NY", "London", "Asia", "NY", "Asia"],
    "pnl": [20, -5, 30, 10, -10, 15]
})

pivot = df.pivot_table(
    index="day",
    columns="session",
    values="pnl",
    fill_value=0
)

print(pivot)