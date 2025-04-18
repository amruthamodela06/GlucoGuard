import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import SMOTE  # type: ignore # Handle imbalanced data

# Step 1: Load Dataset
df = pd.read_csv("diabetes.csv")

# Step 2: Define Features & Target
X = df.drop(columns=["Outcome"])  # Features (excluding Outcome)
Y = df["Outcome"]  # Target variable

# Step 3: Handle Imbalanced Data (if dataset is imbalanced)
smote = SMOTE(random_state=42)
X, Y = smote.fit_resample(X, Y)

# Step 4: Feature Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Step 5: Train-Test Split
X_train, X_test, Y_train, Y_test = train_test_split(X_scaled, Y, test_size=0.2, random_state=42, stratify=Y)

# Step 6: Hyperparameter Tuning (Finding the Best Parameters)
param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4]
}

grid_search = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=5, scoring="accuracy", n_jobs=-1)
grid_search.fit(X_train, Y_train)

# Step 7: Train Random Forest Model with Best Parameters
best_rf = grid_search.best_estimator_
best_rf.fit(X_train, Y_train)


# Step 8: Make Predictions
Y_pred = best_rf.predict(X_test)
# Step 9: Evaluate Accuracy
accuracy = accuracy_score(Y_test, Y_pred)
print(f"✅ Optimized Random Forest Model Accuracy: {accuracy * 100:.2f}%")
