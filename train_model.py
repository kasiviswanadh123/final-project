import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# Step 1: Generate synthetic dataset
np.random.seed(42)
n_samples = 1000

data = pd.DataFrame({
    "Age": np.random.randint(20, 80, n_samples),
    "Gender": np.random.choice([0, 1], n_samples),  # 0=Female, 1=Male
    "Smoking": np.random.choice([0, 1], n_samples),  # 0=No, 1=Yes
    "Alcohol": np.random.choice([0, 1], n_samples),  # 0=No, 1=Yes
    "PhysicalActivity": np.random.choice([0, 1, 2], n_samples),  # 0=Low, 1=Medium, 2=High
    "BMI": np.round(np.random.uniform(18, 40, n_samples), 1),
    "BloodPressure": np.random.choice([0, 1], n_samples),  # 0=Normal, 1=High
    "FamilyHistory": np.random.choice([0, 1], n_samples),  # 0=No, 1=Yes
    "Stress": np.random.choice([0, 1, 2], n_samples)  # 0=Low, 1=Medium, 2=High
})

# Step 2: Create target variable
data["HeartDisease"] = np.where(
    (data["Age"] > 50) |
    (data["Smoking"] == 1) |
    (data["Alcohol"] == 1) |
    (data["BMI"] > 30) |
    (data["BloodPressure"] == 1) |
    (data["FamilyHistory"] == 1) |
    (data["Stress"] == 2), 1, 0
)

# Step 3: Train/test split
X = data.drop("HeartDisease", axis=1)
y = data["HeartDisease"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 4: Train Random Forest model
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Step 5: Save model locally
joblib.dump(model, "heart_disease_model.pkl")
print("✅ Model trained and saved as heart_disease_model.pkl")