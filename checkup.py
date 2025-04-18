from flask import Blueprint, render_template, request, session, redirect
from models import db, PredictionHistory
import numpy as np
from train_model import best_rf, scaler  # Import trained model and scaler

checkup = Blueprint('checkup', __name__)

@checkup.route('/checkup', methods=['GET', 'POST'])
def checkup_view():
    if 'user_id' not in session:
        return redirect('/login')

    result = None
    color_class = None

    if request.method == 'POST':
        try:
            if 'predict_risk' in request.form:
                # Handle risk prediction
                input_data = [
                    float(request.form['Pregnancies']),
                    float(request.form['Glucose']),
                    float(request.form['BloodPressure']),
                    float(request.form['SkinThickness']),
                    float(request.form['Insulin']),
                    float(request.form['BMI']),
                    float(request.form['DiabetesPedigreeFunction']),
                    float(request.form['Age']),
                ]

                # Scale input and get probability
                input_scaled = scaler.transform([input_data])
                probability = best_rf.predict_proba(input_scaled)[0][1]
                risk_percent = round(probability * 100, 2)

                # Interpretation logic
                if risk_percent < 30:
                    label = "Very Low Risk"
                    color_class = "very-low"
                elif 30 <= risk_percent < 50:
                    label = "Moderate Risk"
                    color_class = "moderate"
                elif 50 <= risk_percent < 70:
                    label = "High Risk"
                    color_class = "high"
                else:
                    label = "Very High Risk"
                    color_class = "very-high"

                risk = f"Risk of Diabetes: {risk_percent}% – {label}"
                result = risk

                # Save prediction to DB
                history = PredictionHistory(
                    prediction=risk,
                    user_id=session['user_id'],
                    glucose=input_data[1],
                    bp=input_data[2],
                    bmi=input_data[5],
                    age=int(input_data[7])
                )
                db.session.add(history)
                db.session.commit()

        except Exception as e:
            result = "An error occurred. Please check your inputs."
            color_class = "error"

    return render_template('checkup.html', result=result, color_class=color_class)

@checkup.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    history = PredictionHistory.query.filter_by(user_id=user_id).order_by(PredictionHistory.timestamp.desc()).all()
    return render_template('history.html', history=history)