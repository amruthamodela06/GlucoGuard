from flask import Flask, render_template, url_for, request, session, redirect, flash, jsonify
from models import db, User, EmotionLog, DailyPlan, UserPreferences, PredictionHistory
from datetime import date
from auth import auth
from checkup import checkup
from flask import make_response
from io import BytesIO
from xhtml2pdf import pisa
from functools import wraps
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()  # Add at the top

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(auth)
app.register_blueprint(checkup)

# Custom login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

@app.route('/')
def index():
    print("Index route, session:", session)
    if 'user_id' in session:
        print("Redirecting to dashboard")
        return redirect('/dashboard')
    return render_template('index.html', hide_navbar=True)

@app.route('/dashboard', methods=['GET', 'POST'], endpoint='dashboard')
@login_required
def dashboard():
    if not session.get('user_id'):
        return jsonify({'error': 'Unauthorized'}), 401

    user = db.session.get(User, session['user_id'])
    if not user:
        flash("Session expired or user not found. Please log in again.")
        session.pop('user_id', None)
        return jsonify({'error': 'Session expired'}), 401

    name = session.get('name')
    selected_diet = session.get('diet') or "veg"

    def get_mood_tip(mood):
        return {
            "Happy": "Keep smiling! Share your joy today 😊",
            "Stressed": "Try breathing exercises or a short walk 🌿",
            "Tired": "Rest well, and hydrate. A power nap helps 😴",
            "Energetic": "Perfect time for a light workout 💪"
        }.get(mood, "")

    def get_meal_plan(diet, allergy, risk_level):
        allergies = [a.strip().lower() for a in allergy.split(',')] if allergy else []
        veg = {
            "morning": "Oats with almond milk",
            "lunch": "Quinoa & paneer salad",
            "evening": "Methi water with roasted chana",
            "dinner": "Khichdi with bottle gourd",
            "juice": "Amla-mint shot"
        }
        nonveg = {
            "morning": "Boiled eggs & multigrain toast",
            "lunch": "Grilled chicken & veggies",
            "evening": "Buttermilk with flaxseeds",
            "dinner": "Steamed fish & brown rice",
            "juice": "Bitter gourd + lemon blend"
        }
        nonveg_allergies = ['mutton', 'fish', 'egg']
        base = veg if diet == 'veg' else nonveg
        safe_plan = {}

        for key, val in base.items():
            modified_val = val
            for item in allergies:
                if diet == 'nonveg' and any(a in val.lower() for a in nonveg_allergies):
                    for allergen in nonveg_allergies:
                        if allergen in val.lower():
                            modified_val = val.replace(allergen, "safe alternative")
                elif item in val.lower():
                    modified_val = val.replace(item, "safe alternative")
            safe_plan[key] = modified_val

        if risk_level == 'none':
            safe_plan["note"] = "You're doing great! Keep eating clean 🌱"

        return safe_plan

    if request.method == "POST":
        action = request.form.get("action")
        response_data = {}

        if action == "log_mood":
            mood = request.form.get("mood")
            notes = request.form.get("notes", "")
            if not mood:
                return jsonify({'error': 'Mood is required'}), 400

            mood_log = EmotionLog(mood=mood, notes=notes, user_id=session['user_id'])
            db.session.add(mood_log)
            db.session.commit()
            response_data = {
                'mood_message': f"Mood '{mood}' logged successfully!",
                'wellness_tip': get_mood_tip(mood)
            }

        elif action == "save_prefs":
            diet = request.form.get("diet")
            user_allergy_input = request.form.get("allergy", "").strip()
            allergy = user_allergy_input if user_allergy_input else ""

            session['diet'] = diet

            pref = UserPreferences.query.filter_by(user_id=session['user_id']).first()
            if pref:
                pref.dietary_preference = diet
                pref.allergies = allergy
            else:
                pref = UserPreferences(user_id=session['user_id'], dietary_preference=diet, allergies=allergy)
                db.session.add(pref)
            db.session.commit()

            risk = getattr(user, 'diabetes_risk', 'low')
            plan = get_meal_plan(diet, allergy, risk)

            existing = DailyPlan.query.filter_by(user_id=session['user_id'], date=date.today()).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
            new_plan = DailyPlan(
                user_id=session['user_id'],
                date=date.today(),
                morning=plan['morning'],
                lunch=plan['lunch'],
                evening=plan['evening'],
                dinner=plan['dinner'],
                juice=plan['juice']
            )
            db.session.add(new_plan)
            db.session.commit()

            response_data = {
                'pref_message': "Preferences saved!",
                'meal_tip': {
                    'morning': plan['morning'],
                    'lunch': plan['lunch'],
                    'evening': plan['evening'],
                    'dinner': plan['dinner'],
                    'juice': plan['juice'],
                    'note': plan.get('note', '')
                }
            }

        else:
            return jsonify({'error': 'Invalid action'}), 400

        return jsonify(response_data)

    # For GET requests, render the template without meal_plan
    mood_message = session.pop('mood_message', None)
    pref = UserPreferences.query.filter_by(user_id=session['user_id']).first()
    allergy = pref.allergies if pref else ""

    return render_template('dashboard.html',
                           name=name,
                           mood_message=mood_message,
                           wellness_tip=None,
                           pref_message=None,
                           selected_diet=selected_diet,
                           meal_tip=None,  # Ensure meal_tip is None on page load
                           selected_allergy=allergy,
                           predictions=[p.prediction for p in user.predictions] if user else [])

@app.route('/download-history', endpoint='download_history')
@login_required
def download_history():
    user = db.session.get(User, session['user_id'])
    print("User object:", user)  # Add this line to debug
    predictions = user.predictions
    html = render_template('history_pdf_template.html', predictions=predictions, user=user)
    pdf = BytesIO()
    pisa.CreatePDF(BytesIO(html.encode("utf-8")), dest=pdf)
    response = make_response(pdf.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=prediction_history.pdf'
    return response


@app.route('/chat', methods=['POST'])
@login_required
def chat():
    message = request.json.get('message')
    user = db.session.get(User, session['user_id'])
    if not message or not user:
        return jsonify({"reply": "Unable to process request."})

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        context = f"""
        You are a diabetes-focused assistant. User details: 
        - Diet: {user.preferences.dietary_preference if user.preferences else 'unknown'}
        - Allergies: {user.preferences.allergies if user.preferences else 'none'}
        - Diabetes risk: {getattr(user, 'diabetes_risk', 'low')}
        - Mood: {EmotionLog.query.filter_by(user_id=session['user_id']).order_by(EmotionLog.timestamp.desc()).first().mood if EmotionLog.query.filter_by(user_id=session['user_id']).first() else 'unknown'}
        Answer in 3-4 lines, focusing on diabetes, meals (low-GI), or exercise tailored to user data.
        """
        prompt = f"{context}\nUser: {message}"
        response = model.generate_content(prompt)
        reply = response.text.strip() if response.text else "Try again later."
    except Exception as e:
        print(f"Gemini error: {str(e)}")
        reply = "Error processing request."

    return jsonify({"reply": reply})

@app.route('/checkup', methods=['GET', 'POST'])
def checkup():
    return render_template("checkup.html")

# Create tables
with app.app_context():
    db.create_all()

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 5000 if PORT not set
    app.run(host='0.0.0.0', port=port)
