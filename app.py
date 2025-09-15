from flask import Flask, render_template, redirect, url_for, session, flash, request
import bcrypt
from flask_mysqldb import MySQL
import MySQLdb.cursors
import joblib
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ravi'

# Database Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'ravi_db'
mysql = MySQL(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

with open("heart_disease_model.pkl", "rb") as f:
    model = joblib.load("heart_disease_model.pkl")

# -------------------- Routes --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

            if not all([name, email, password]):
                flash('All fields are required!', 'error')
                return redirect(url_for('register'))

            if '@' not in email:
                flash('Please enter a valid email address!', 'error')
                return redirect(url_for('register'))

            if len(password) < 6:
                flash('Password must be at least 6 characters long!', 'error')
                return redirect(url_for('register'))

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id FROM eren WHERE email=%s", (email,))
            if cursor.fetchone():
                flash('Email already exists!', 'error')
                cursor.close()
                return redirect(url_for('register'))

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO eren (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            mysql.connection.commit()
            cursor.close()

            flash('✅ Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM eren WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            stored_hash = user[3]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash("Welcome back!", "success")
                return redirect(url_for('dashboard'))

        flash("Login failed. Please check your email and password", "error")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM eren WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        return redirect(url_for('login'))

    username = session.get('username') or 'User'
    return render_template('dashboard.html', user=user, username=username)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/tips')
def tips():
    if 'user_id' not in session:
        flash("Please log in to access health tips.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM eren WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        return redirect(url_for('login'))

    username = session.get('username') or 'User'
    return render_template('tips.html', user=user, username=username)

@app.route('/health')
def health():
    return render_template('health.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        total_score = 0
        for i in range(1, 9):
            answer = request.form.get(f'q{i}')
            if answer and answer.isdigit():
                total_score += int(answer)

        health_percentage = max(0, 100 - total_score)
        return redirect(url_for('result', score=health_percentage))

    return render_template('quiz.html')

@app.route('/result')
def result():
    score = request.args.get('score', 0)
    try:
        score = int(score)
    except ValueError:
        score = 0

    if score >= 80:
        risk_level = "Low Risk"
        message = "Excellent health! Keep it up."
    elif score >= 50:
        risk_level = "Moderate Risk"
        message = "Good health, but there's room for improvement."
    else:
        risk_level = "High Risk"
        message = "Significant risks detected. Consult a doctor."

    return render_template(
        'result.html',
        score=score,
        risk_level=risk_level,
        message=message
    )

@app.route('/workout')
def workout():
    if 'user_id' not in session:
        flash("Please log in to access workouts.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM eren WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        return redirect(url_for('login'))

    username = session.get('username') or 'User'
    return render_template('workout.html', user=user, username=username)

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if 'user_id' not in session:
        flash("Please log in to book an appointment.", "warning")
        return redirect(url_for('login'))

    # Get list of doctors for the dropdown
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, full_name, specialization FROM doctor")
    doctors = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        try:
            # Debug: print all form data
            logger.debug("Form data received: %s", dict(request.form))
            
            patient_id = session['user_id']
            doctor_id = request.form.get('doctor_id')
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            preferred_date = request.form.get('preferred_date')
            time_slot = request.form.get('time_slot')
            
            # Validate required fields
            if not all([doctor_id, full_name, email, preferred_date, time_slot]):
                missing = []
                if not doctor_id: missing.append("doctor")
                if not full_name: missing.append("full name")
                if not email: missing.append("email")
                if not preferred_date: missing.append("date")
                if not time_slot: missing.append("time slot")
                flash(f"❌ Missing required fields: {', '.join(missing)}", "error")
                return render_template('appointment.html', doctors=doctors, form_data=request.form)
            
            # Convert checkbox values to booleans
            chest_pain = 'chest_pain' in request.form
            shortness_of_breath = 'shortness_of_breath' in request.form
            palpitations = 'palpitations' in request.form
            dizziness = 'dizziness' in request.form
            fatigue = 'fatigue' in request.form
            swelling_in_legs = 'swelling_in_legs' in request.form

            additional_details = request.form.get('additional_details', '')
            is_urgent = chest_pain or shortness_of_breath

            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO appointments 
                (patient_id, doctor_id, full_name, email, preferred_date, time_slot, 
                 chest_pain, shortness_of_breath, palpitations, dizziness, 
                 fatigue, swelling_in_legs, additional_details, is_urgent) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id, doctor_id, full_name, email, preferred_date, time_slot,
                chest_pain, shortness_of_breath, palpitations, dizziness,
                fatigue, swelling_in_legs, additional_details, is_urgent
            ))

            mysql.connection.commit()
            cursor.close()

            flash("✅ Appointment booked successfully!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            logger.error("Error booking appointment: %s", str(e))
            flash(f"❌ Failed to book appointment: {str(e)}", "error")
            # Return to form with submitted data preserved
            return render_template('appointment.html', doctors=doctors, form_data=request.form)

    return render_template('appointment.html', doctors=doctors)

@app.route('/doctor_registration', methods=['GET', 'POST'])
def doctor_register():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            license_number = request.form.get('license_number')
            specialization = request.form.get('specialization')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validate inputs
            if not all([full_name, email, license_number, specialization, password, confirm_password]):
                flash("❌ All fields are required!", "danger")
                return redirect(url_for('doctor_register'))

            if len(password) < 8:
                flash("❌ Password must be at least 8 characters long!", "danger")
                return redirect(url_for('doctor_register'))

            if password != confirm_password:
                flash("❌ Passwords do not match!", "danger")
                return redirect(url_for('doctor_register'))

            # Check if email already exists
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id FROM doctor WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("❌ Email already registered! Please use a different email.", "danger")
                cursor.close()
                return redirect(url_for('doctor_register'))

            hashed_password = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO doctor (full_name, email, license_number, specialization, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (full_name, email, license_number, specialization, hashed_password))

            mysql.connection.commit()
            cursor.close()

            flash("✅ Registration successful! Please log in with your credentials.", "success")
            return redirect(url_for('doctor_login'))

        except Exception as e:
            print(f"Error in doctor registration: {str(e)}")
            flash("❌ Registration failed. Please try again.", "danger")
            return redirect(url_for('doctor_register'))

    return render_template('doctor_registration.html')

@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("❌ Email and password are required", "danger")
            return redirect(url_for('doctor_login'))

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM doctor WHERE email = %s", (email,))
            doctor = cursor.fetchone()
            cursor.close()

            if doctor and check_password_hash(doctor['password'], password):
                session['doctor_id'] = doctor['id']
                session['doctor_name'] = doctor['full_name']
                session['doctor_email'] = doctor['email']
                flash(f"✅ Welcome Dr. {doctor['full_name']}!", "success")
                return redirect(url_for('doctor_dashboard'))
            else:
                flash("❌ Invalid email or password", "danger")
                return redirect(url_for('doctor_login'))

        except Exception as e:
            print(f"Doctor login error: {str(e)}")
            flash("❌ Login failed. Please try again.", "danger")
            return redirect(url_for('doctor_login'))

    return render_template('doctor_login.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'doctor_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('doctor_login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get doctor's info
        cursor.execute("SELECT * FROM doctor WHERE id = %s", (session['doctor_id'],))
        doctor = cursor.fetchone()

        # Get appointments ONLY for this doctor
        cursor.execute("""
            SELECT a.*, e.name as patient_name 
            FROM appointments a 
            INNER JOIN eren e ON a.patient_id = e.id 
            WHERE a.doctor_id = %s 
            ORDER BY a.preferred_date, a.time_slot
        """, (session['doctor_id'],))
        appointments = cursor.fetchall()

        # Calculate statistics for THIS DOCTOR only
        total_appointments = len(appointments)
        completed_appointments = sum(1 for appt in appointments if appt.get('status') == 'completed')
        pending_appointments = total_appointments - completed_appointments
        urgent_appointments = sum(1 for appt in appointments if appt.get('is_urgent'))

        cursor.close()

        return render_template(
            'doctor_dashboard.html',
            doctor=doctor,
            appointments=appointments,
            total_appointments=total_appointments,
            completed_appointments=completed_appointments,
            pending_appointments=pending_appointments,
            urgent_appointments=urgent_appointments
        )

    except Exception as e:
        print(f"Error loading doctor dashboard: {str(e)}")
        flash("Error loading dashboard. Please try again.", "danger")
        return redirect(url_for('doctor_login'))

@app.route('/update_appointment_status/<int:appointment_id>', methods=['POST'])
def update_appointment_status(appointment_id):
    if 'doctor_id' not in session:
        flash("Please log in to update appointments.", "warning")
        return redirect(url_for('doctor_login'))
    
    try:
        new_status = request.form.get('status')
        
        if new_status not in ['scheduled', 'completed', 'cancelled']:
            flash("Invalid status.", "danger")
            return redirect(url_for('doctor_dashboard'))
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET status = %s 
            WHERE id = %s AND doctor_id = %s
        """, (new_status, appointment_id, session['doctor_id']))
        
        mysql.connection.commit()
        cursor.close()
        
        flash("Appointment status updated successfully!", "success")
        return redirect(url_for('doctor_dashboard'))
        
    except Exception as e:
        print(f"Error updating appointment status: {str(e)}")
        flash("Error updating appointment status.", "danger")
        return redirect(url_for('doctor_dashboard'))

@app.route("/error")
def error_page():
    message = "This is a test error page."
    return render_template("error.html", message=message)

# -------------------- Prediction with History Storage --------------------
@app.route('/predict', methods=['POST'])
def predict():
    if 'user_id' not in session:
        flash("Please log in to make predictions.", "warning")
        return redirect(url_for('login'))
    
    try:
        age = float(request.form['age'])
        gender = request.form['gender']
        smoking = request.form['smoking']
        alcohol = request.form['alcohol']
        physical_activity = request.form['physical_activity']
        bmi = float(request.form['bmi'])
        bp = request.form['bp']
        family_history = request.form['family_history']
        stress = request.form['stress']

        print("Received inputs:", age, gender, smoking, alcohol, physical_activity, bmi, bp, family_history, stress)

        # Convert categorical to numeric (example encoding)
        gender_val = 1 if gender.lower() == "male" else 0
        smoking_val = 1 if smoking.lower() == "yes" else 0
        alcohol_val = 1 if alcohol.lower() == "yes" else 0
        activity_val = {"low":0, "medium":1, "high":2}[physical_activity.lower()]
        bp_val = 1 if bp.lower() == "high" else 0
        family_val = 1 if family_history.lower() == "yes" else 0
        stress_val = {"low":0, "medium":1, "high":2}[stress.lower()]

        # Final feature vector
        features = [[age, gender_val, smoking_val, alcohol_val, activity_val, bmi, bp_val, family_val, stress_val]]
        print("Features for model:", features)

        prediction = model.predict(features)
        probability = model.predict_proba(features)[0][1] * 100

        result = "Low Risk - No Heart Disease" if prediction[0] == 0 else "High Risk - Possible Heart Disease"
        
        # Determine risk level based on probability
        if probability >= 70:
            risk_level = "High"
        elif probability >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Store prediction in history
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO prediction_history 
            (user_id, age, gender, smoking, alcohol, physical_activity, bmi, bp, family_history, stress, prediction_result, risk_level, probability) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'], age, gender, smoking, alcohol, physical_activity, 
            bmi, bp, family_history, stress, result, risk_level, probability
        ))
        mysql.connection.commit()
        cursor.close()

        details = {
            'result': result,
            'probability': f"{probability:.1f}%",
            'risk_level': risk_level,
            'age': age,
            'gender': gender,
            'smoking': smoking,
            'alcohol': alcohol,
            'physical_activity': physical_activity,
            'bmi': bmi,
            'bp': bp,
            'family_history': family_history,
            'stress': stress
        }

        return render_template("predict.html", prediction=details)

    except Exception as e:
        print("🔥 Error occurred:", e)
        flash("Prediction failed. Please try again.", "error")
        return redirect(url_for('dashboard'))

# -------------------- Prediction History Route --------------------
# Add this new route to your existing Flask app
@app.route('/history')
def history():
    if 'user_id' not in session:
        flash("Please log in to view your history.", "warning")
        return redirect(url_for('login'))
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT id, age, gender, smoking, alcohol, physical_activity, bmi, bp, 
                   family_history, stress, prediction_result, risk_level, probability, created_at 
            FROM prediction_history 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (session['user_id'],))
        history_data = cursor.fetchall()
        cursor.close()
        
        # Prepare data for charts
        chart_data = {
            'dates': [],
            'risk_scores': [],
            'cholesterol_levels': []  # We'll use BMI as a proxy for cholesterol in this example
        }
        
        for record in history_data:
            chart_data['dates'].append(record['created_at'].strftime('%Y-%m-%d'))
            chart_data['risk_scores'].append(record['probability'])
            chart_data['cholesterol_levels'].append(record['bmi'] * 10)  # Scale BMI to simulate cholesterol
        
        return render_template('history.html', 
                             history=history_data, 
                             chart_data=chart_data,
                             username=session.get('username'))
        
    except Exception as e:
        print(f"Error retrieving history: {str(e)}")
        flash("Error retrieving prediction history.", "error")
        return redirect(url_for('dashboard'))

# -------------------- Startup DB Check --------------------
def check_database_connection():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()[0]
        print(f"✅ Successfully connected to database: {db_name}")
        
        # Check if appointments table exists
        cursor.execute("SHOW TABLES LIKE 'appointments'")
        if not cursor.fetchone():
            print("❌ Appointments table doesn't exist. Creating it now...")
            # Create the appointments table
            cursor.execute("""
                CREATE TABLE appointments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    doctor_id INT NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    preferred_date DATE NOT NULL,
                    time_slot VARCHAR(50) NOT NULL,
                    chest_pain BOOLEAN DEFAULT FALSE,
                    shortness_of_breath BOOLEAN DEFAULT FALSE,
                    palpitations BOOLEAN DEFAULT FALSE,
                    dizziness BOOLEAN DEFAULT FALSE,
                    fatigue BOOLEAN DEFAULT FALSE,
                    swelling_in_legs BOOLEAN DEFAULT FALSE,
                    additional_details TEXT,
                    is_urgent BOOLEAN DEFAULT FALSE,
                    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES eren(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
                )
            """)
            print("✅ Appointments table created successfully")
        
        # Check if prediction_history table exists
        cursor.execute("SHOW TABLES LIKE 'prediction_history'")
        if not cursor.fetchone():
            print("❌ Prediction history table doesn't exist. Creating it now...")
            # Create the prediction_history table
            cursor.execute("""
                CREATE TABLE prediction_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    age FLOAT NOT NULL,
                    gender VARCHAR(10) NOT NULL,
                    smoking VARCHAR(3) NOT NULL,
                    alcohol VARCHAR(3) NOT NULL,
                    physical_activity VARCHAR(10) NOT NULL,
                    bmi FLOAT NOT NULL,
                    bp VARCHAR(10) NOT NULL,
                    family_history VARCHAR(3) NOT NULL,
                    stress VARCHAR(10) NOT NULL,
                    prediction_result VARCHAR(50) NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    probability FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES eren(id) ON DELETE CASCADE
                )
            """)
            print("✅ Prediction history table created successfully")
        
        cursor.close()
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        check_database_connection()
    app.run(debug=True)