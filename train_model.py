import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import SMOTE
import joblib

def train_and_save():
    # Step 1: Load Dataset
    df = pd.read_csv("diabetes.csv")

    # Step 2: Define Features & Target
    X = df.drop(columns=["Outcome"])  # Features (excluding Outcome)
    Y = df["Outcome"]  # Target variable

    # Step 3: Handle Imbalanced Data (if dataset is imbalanced)
    X, Y = SMOTE(random_state=42).fit_resample(X, Y)

    # Step 4: Feature Scaling
    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    # Step 5: Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, Y, test_size=0.2, random_state=42, stratify=Y
    )

    # Step 6: Hyperparameter Tuning (Finding the Best Parameters)
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [10, 20, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    }

    grid = GridSearchCV(RandomForestClassifier(random_state=42),
                        param_grid, cv=5, scoring="accuracy", n_jobs=-1)
    grid.fit(X_train, y_train)

    # Step 7: Train Random Forest Model with Best Parameters
    best_rf = grid.best_estimator_
    best_rf.fit(X_train, y_train)

    # save artifacts
    joblib.dump(best_rf, "models/best_rf.joblib")
    joblib.dump(scaler, "models/scaler.joblib")
    print("Model + scaler saved.")

if __name__ == "__main__":
    train_and_save()