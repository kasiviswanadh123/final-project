import streamlit as st
import joblib
import numpy as np

# Load retrained local model
model = joblib.load("heart_disease_model.pkl")

st.title("❤ Heart Disease Prediction App")
st.write("Enter your details below to check the risk of heart disease:")

# User Inputs
age = st.number_input("Age", min_value=10, max_value=100, value=30)
gender = st.selectbox("Gender", ["Female", "Male"])  # 0=Female, 1=Male
smoking = st.selectbox("Smoking Habit", ["No", "Yes"])  # 0=No, 1=Yes
alcohol = st.selectbox("Alcohol Consumption", ["No", "Yes"])  # 0=No, 1=Yes
physical_activity = st.selectbox("Physical Activity Level", ["Low", "Medium", "High"])  # 0,1,2
bmi = st.number_input("BMI (Body Mass Index)", min_value=10.0, max_value=50.0, value=22.0)
bp = st.selectbox("Blood Pressure Status", ["Normal", "High"])  # 0=Normal, 1=High
family_history = st.selectbox("Family History of Heart Disease", ["No", "Yes"])  # 0=No, 1=Yes
stress = st.selectbox("Stress Level", ["Low", "Medium", "High"])  # 0,1,2

# Encoding user input (matches training encoding)
gender_map = {"Female": 0, "Male": 1}
smoking_map = {"No": 0, "Yes": 1}
alcohol_map = {"No": 0, "Yes": 1}
physical_map = {"Low": 0, "Medium": 1, "High": 2}
bp_map = {"Normal": 0, "High": 1}
family_map = {"No": 0, "Yes": 1}
stress_map = {"Low": 0, "Medium": 1, "High": 2}

# Prepare input for model
features = np.array([[
    age,
    gender_map[gender],
    smoking_map[smoking],
    alcohol_map[alcohol],
    physical_map[physical_activity],
    bmi,
    bp_map[bp],
    family_map[family_history],
    stress_map[stress]
]])

# Prediction
if st.button("Predict"):
    prediction = model.predict(features)[0]
    if prediction == 1:
        st.error("⚠ High Risk: This person may have heart disease.")
    else:
        st.success("✅ Low Risk: This person is unlikely to have heart disease.")