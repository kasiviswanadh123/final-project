import pickle
import joblib
import numpy as np

# --- Load your model here ---
with open("heart_disease_model.pkl", "rb") as f:
    model = pickle.load(f)
# OR if saved with joblib, try:
# model = joblib.load("model.pkl")

# --- Check what it really is ---
print("Type of model:", type(model))

# Check if it has predict method
if hasattr(model, "predict"):
    print("✅ This is a trained model. You can use model.predict().")
elif isinstance(model, np.ndarray):
    print("❌ This is just a NumPy array. It has no predict().")
else:
    print("⚠️ This is not a NumPy array, but also not a model with predict().")
    print("Available attributes:", dir(model))
