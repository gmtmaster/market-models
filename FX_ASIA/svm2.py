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
        RAsia = HAsia - LAsia  # Asia session range
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
        
        # Rule-Based Features
        Rule_1 = 1 if ODay - MAsia > 0 else 0
        median_RAsia = np.median([row[4] for row in data_list]) if data_list else RAsia
        Rule_2 = 1 if ODay > MAsia and RAsia > median_RAsia else 0
        
        if Y is not None:
            data_list.append([HAsia, LAsia, MAsia, ODay, RAsia, Rule_1, Rule_2, Y])
        
        current_date += timedelta(days=1)

    df = pd.DataFrame(data_list, columns=["HAsia", "LAsia", "MAsia", "ODay", "RAsia", "Rule_1", "Rule_2", "Y"])
    df = df.dropna(subset=["Y"])
    return df

# Load data
df = load_data()
start_date = datetime(2022, 1, 1)
end_date = datetime(2025, 3, 24)
dataset = prepare_dataset(df, start_date, end_date)

# Split data
X = dataset[["HAsia", "LAsia", "MAsia", "ODay", "RAsia", "Rule_1", "Rule_2"]]
y = dataset["Y"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scaling the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Create the SVM model
svm_model = SVC(probability=True, random_state=42)  # Set probability=True

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

# Predictions with the best model (using probabilities)
y_pred_proba_svm = best_svm_model.predict_proba(X_test_scaled)

# Rule Modifications: Adjust the probabilities based on the rules
def adjust_probability_with_rules(probabilities, X):
    rule_1 = X[:, 5]  # Rule_1 column
    rule_2 = X[:, 6]  # Rule_2 column
    
    # Rule 1: If ODay > MAsia, increase probability of Y=1
    probabilities[:, 1] += rule_1 * 0.02  # Add 5% probability for Y=1
    probabilities[:, 0] -= rule_1 * 0.02  # Subtract 5% probability for Y=0
    
    # Rule 2: If ODay > MAsia and RAsia > median(RAsia), increase probability of Y=1
    probabilities[:, 1] += rule_2 * 0.02  # Add 5% probability for Y=1
    probabilities[:, 0] -= rule_2 * 0.02  # Subtract 5% probability for Y=0
    
    # Ensure probabilities stay between 0 and 1
    probabilities = np.clip(probabilities, 0, 1)
    
    return probabilities

# Adjust probabilities using the rules
adjusted_probabilities = adjust_probability_with_rules(y_pred_proba_svm, X_test_scaled)

# Convert adjusted probabilities to predictions (if > 0.5, predict 1, else predict 0)
y_pred_adjusted = (adjusted_probabilities[:, 1] > 0.5).astype(int)

# Accuracy and confusion matrix for SVM with rule adjustments
svm_accuracy = accuracy_score(y_test, y_pred_adjusted)
svm_conf_matrix = confusion_matrix(y_test, y_pred_adjusted)

print(f"SVM Accuracy (Tuned with Rule Adjustments): {svm_accuracy * 100:.2f}%")
print(svm_conf_matrix)
