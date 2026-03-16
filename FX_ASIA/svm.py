import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from asia_europe_date_import import load_data, fetch_asia_session_data, fetch_european_session_data
from datetime import datetime, timedelta

def prepare_dataset(df, start_date, end_date):
    data_list = []
    current_date = start_date
    
    while current_date <= end_date:
        asia_data, HAsia, LAsia, ODay = fetch_asia_session_data(df, current_date)
        europe_data, europe_high, europe_low = fetch_european_session_data(df, current_date)
        
        if asia_data is None or europe_data is None:
            current_date += timedelta(days=1)
            continue
        
        MAsia = (HAsia + LAsia) / 2
        Y = None

        first_high_break = europe_data[europe_data["ask_h"] >= HAsia].head(1)
        first_low_break = europe_data[europe_data["bid_l"] <= LAsia].head(1)

        if not first_high_break.empty and not first_low_break.empty:
            if first_high_break.index[0] < first_low_break.index[0]:
                Y = 1  # Upward breach first
            else:
                Y = 0  # Downward breach first
        elif not first_high_break.empty:
            Y = 1  # Only upward breach
        elif not first_low_break.empty:
            Y = 0  # Only downward breach
        
        if Y is not None:
            data_list.append([HAsia, LAsia, MAsia, ODay, Y, current_date])
        
        current_date += timedelta(days=1)

    df = pd.DataFrame(data_list, columns=["HAsia", "LAsia", "MAsia", "ODay", "Y", "Date"])
    df = df.dropna(subset=["Y"])
    return df

# Load data
df = load_data()
start_date = datetime(2022, 1, 1)
end_date = datetime(2025, 3, 24)
dataset = prepare_dataset(df, start_date, end_date)

# Split data
X = dataset[["HAsia", "LAsia", "MAsia", "ODay"]]
y = dataset["Y"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scaling the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Create the SVM model
svm_model = SVC(random_state=42, probability=True)

# Set up the parameter grid for hyperparameter tuning
param_grid = {
    'C': [0.1, 1, 10, 100],
    'kernel': ['linear', 'poly', 'rbf', 'sigmoid'],
    'gamma': ['scale', 'auto'],
    'class_weight': [None, 'balanced']
}

# Use GridSearchCV to find the best parameters
grid_search = GridSearchCV(svm_model, param_grid, cv=5, n_jobs=-1, verbose=2)
grid_search.fit(X_train_scaled, y_train)

# Get the best model from GridSearchCV
best_svm_model = grid_search.best_estimator_

# Predictions with the best model
y_pred_svm = best_svm_model.predict(X_test_scaled)
y_pred_proba_svm = best_svm_model.predict_proba(X_test_scaled)  # Get the predicted probabilities

# If the dataset is larger than the predictions, slice the dataset to match the length of predictions
if len(dataset) > len(y_pred_proba_svm):
    dataset = dataset.iloc[:len(y_pred_proba_svm)]

# Create DataFrame from predictions and probabilities
results_df = pd.DataFrame({
    'Date': dataset['Date'],  # Add the Date column
    'Prediction': y_pred_svm,  # Predictions (0 or 1)
    'Probability_0': y_pred_proba_svm[:, 0],  # Probability for class 0 (short)
    'Probability_1': y_pred_proba_svm[:, 1]   # Probability for class 1 (long)
})

# Group by date and aggregate probabilities (mean)
df_aggregated = results_df.groupby('Date').agg({
    'Probability_0': 'mean',  # Averaging Probability_0 (short)
    'Probability_1': 'mean',  # Averaging Probability_1 (long)
}).reset_index()

# Add a column to show whether the prediction is for "long" or "short"
df_aggregated['Prediction'] = (df_aggregated['Probability_1'] > df_aggregated['Probability_0']).astype(int)

# Display the result
print(df_aggregated)


# Accuracy and confusion matrix for SVM
svm_accuracy = accuracy_score(y_test, y_pred_svm)
svm_conf_matrix = confusion_matrix(y_test, y_pred_svm)
print(f"SVM Accuracy (Tuned): {svm_accuracy * 100:.2f}%")
print(svm_conf_matrix)
