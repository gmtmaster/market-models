import pandas as pd

data = {
    "trader": ["Adam" ,"Adam", "Adam", "Adam", "Adam"],
    "result": [20, -5, 15, -10, 30],
    "session": ["London", "NY", "Asia", "London", "NY"]
}

df = pd.DataFrame(data)

max_win = (df.sort_values("result", ascending=True))
min_win = (df.sort_values("result", ascending=False))

trade_per_sess = (df.groupby("session")["result"].count())
avg_per_sess = (df.groupby("session")["result"].mean())
sum_per_sess = (df.groupby("session")["result"].sum())





print(max_win)
print(min_win)
print(trade_per_sess)
print(avg_per_sess)
print(sum_per_sess)