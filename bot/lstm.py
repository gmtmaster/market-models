import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# Load and preprocess the data
data = yf.download('EURUSD=X', start='2010-01-01', end='2012-01-01', auto_adjust=True)

# Compute some technical indicators (e.g., SMA, RSI, MACD)
data['SMA_50'] = data['Close'].rolling(window=50).mean()
data['SMA_200'] = data['Close'].rolling(window=200).mean()

# Calculate RSI
delta = data['Close'].pct_change().fillna(0)
gain = np.maximum(delta, 0)  # Positive changes
loss = np.maximum(-delta, 0)  # Negative changes

# Calculate rolling averages
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()

# Calculate RS (Relative Strength) and RSI (Relative Strength Index)
rs = avg_gain / avg_loss
data['RSI'] = 100 - (100 / (1 + rs))

# Drop rows with NaN values (from the rolling window)
data.dropna(inplace=True)

# Scale the data using MinMaxScaler (standard practice for LSTM models)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[['Close', 'SMA_50', 'SMA_200', 'RSI']])

# Define the number of time steps (lookback period) - for example, 10 days
lookback = 10
X = []
y = []

# Prepare the dataset for LSTM (use the last `lookback` days to predict the next day's closing price)
for i in range(lookback, len(scaled_data)):
    X.append(scaled_data[i - lookback:i])  # Use past 'lookback' days as features
    y.append(scaled_data[i, 0])  # Predict the 'Close' price

X = np.array(X, dtype=np.float32)  # Ensure dtype is float32 for compatibility
y = np.array(y, dtype=np.float32)  # Ensure dtype is float32 for compatibility

# Convert to PyTorch tensors
X = torch.tensor(X, dtype=torch.float32)
y = torch.tensor(y, dtype=torch.float32)

# Ensure that X and y are both numpy arrays with compatible data types
X = X.numpy()  # Convert X to numpy array
y = y.numpy()  # Convert y to numpy array

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define the LSTM model
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_layer_size, output_size):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_layer_size, batch_first=True)
        self.linear = nn.Linear(hidden_layer_size, output_size)
    
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        predictions = self.linear(lstm_out[:, -1, :])  # Get the output from the last time step
        return predictions

# Initialize the model, loss function, and optimizer
input_size = X_train.shape[2]  # Number of features (Close, SMA_50, SMA_200, RSI)
hidden_layer_size = 50
output_size = 1  # We're predicting just one value (Close)
model = LSTMModel(input_size, hidden_layer_size, output_size)

# Set loss function and optimizer
loss_function = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Train the model
epochs = 100
for epoch in range(epochs):
    model.train()
    optimizer.zero_grad()  # Zero the gradients
    y_pred = model(torch.tensor(X_train, dtype=torch.float32))  # Forward pass
    loss = loss_function(y_pred, torch.tensor(y_train, dtype=torch.float32).unsqueeze(1))  # Compute loss
    loss.backward()  # Backpropagation
    optimizer.step()  # Update weights
    
    if (epoch + 1) % 10 == 0:
        print(f'Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}')

# Test the model
model.eval()
with torch.no_grad():
    y_pred = model(torch.tensor(X_test, dtype=torch.float32))

# Evaluate the model
y_pred = y_pred.numpy().flatten()  # Flatten the predictions
y_test = y_test.flatten()  # Flatten the actual values
mse = np.mean((y_pred - y_test) ** 2)
print(f'Mean Squared Error: {mse}')

# Assuming `y_pred` and `y_test` are already defined

# Tracking values
buy_signals = []
sell_signals = []
stop_loss_triggered = []
take_profit_triggered = []

# Initialize tracking variables
initial_balance = 1000  # Start with $1000
balance = initial_balance
position = 0  # No position initially
entry_price = 0
stop_loss_percentage = 0.01  # 1% stop loss
take_profit_percentage = 0.03  # 3% take profit
portfolio_values = [balance]  # Track portfolio value over time
dates = [data.index[0]]  # Track the corresponding dates of portfolio values
profit_loss = [0]  # Track profit or loss for each trade (initially 0)

# Simulating the trading process
for i in range(1, len(y_pred)):
    if position == 0:  # No active position
        # Buy signal: Trigger a buy order at the predicted price
        if y_pred[i] > y_test[i - 1]:
            position = balance / y_test[i]  # Buy at the current price
            entry_price = y_test[i]
            print(f"Buy signal at {data.index[-len(y_pred):][i]} - Entry price: {entry_price}")
    
    elif position > 0:  # We have an active position
        # Check if price hits the stop loss or take profit
        current_price = y_test[i]
        
        # Check for stop loss condition (1% below entry price)
        if current_price <= entry_price * (1 - stop_loss_percentage):
            balance = position * current_price  # Sell at current price
            profit_loss.append(balance - initial_balance)  # Calculate profit or loss
            portfolio_values.append(balance)  # Track portfolio value
            dates.append(data.index[-len(y_pred):][i])  # Add the current date
            position = 0  # Exit the position
            print(f"Stop loss triggered at {data.index[-len(y_pred):][i]} - Price: {current_price}")
        
        # Check for take profit condition (3% above entry price)
        elif current_price >= entry_price * (1 + take_profit_percentage):
            balance = position * current_price  # Sell at current price
            profit_loss.append(balance - initial_balance)  # Calculate profit or loss
            portfolio_values.append(balance)  # Track portfolio value
            dates.append(data.index[-len(y_pred):][i])  # Add the current date
            position = 0  # Exit the position
            print(f"Take profit triggered at {data.index[-len(y_pred):][i]} - Price: {current_price}")
        
        # If neither stop loss nor take profit is triggered, continue holding the position
        elif y_pred[i] < y_test[i - 1]:  # Sell signal based on the model
            balance = position * current_price  # Sell at the current price
            profit_loss.append(balance - initial_balance)  # Calculate profit or loss
            portfolio_values.append(balance)  # Track portfolio value
            dates.append(data.index[-len(y_pred):][i])  # Add the current date
            position = 0  # Exit the position
            print(f"Sell signal at {data.index[-len(y_pred):][i]} - Price: {current_price}")

    # If no trade happened, continue adding the current portfolio value for the next date
    if len(portfolio_values) < len(dates):
        portfolio_values.append(portfolio_values[-1])
        dates.append(data.index[-len(y_pred):][i])
        profit_loss.append(profit_loss[-1])  # Add a 0 for the missing profit/loss entry

# Now we can plot the portfolio values and P&L

# Plot portfolio value and P&L
plt.figure(figsize=(12, 6))
plt.plot(dates, portfolio_values, label='Portfolio Value', color='blue')
plt.title('Portfolio Value Over Time with Stop Loss and Take Profit')
plt.xlabel('Date')
plt.ylabel('Portfolio Value ($)')
plt.legend()
plt.grid(True)

# Plot Profit/Loss over time
plt.figure(figsize=(12, 6))
plt.plot(dates, np.cumsum(profit_loss), label='Cumulative Profit/Loss', color='green')
plt.title('Cumulative Profit/Loss Over Time')
plt.xlabel('Date')
plt.ylabel('Profit/Loss ($)')
plt.legend()
plt.grid(True)

plt.show()

