trades = [25, -10, 40, -5, 30]

total_profit = sum(trades)

wins = 0
for trade in trades:
    if trade > 0:
        wins += 1


winrate = wins / len(trades)


win_sum = 0
win_count = 0

for trade in trades:
    if trade > 0:
        win_sum += trade
        win_count += 1


average_win = win_sum / win_count

loss_sum = 0
loss_count = 0

for trade in trades:
    if trade < 0:
        loss_sum += trade
        loss_count += 1


average_loss = loss_sum / loss_count

expectancy = (winrate * average_win) + ((1-winrate) * average_loss)


print(total_profit)
print(winrate)
print(average_win)
print(average_loss)
print(expectancy)