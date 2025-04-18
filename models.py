from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100))  # Add this only if you're using 'name' in forms/templates
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relationships
    predictions = db.relationship('PredictionHistory', backref='user', lazy=True)
    emotions = db.relationship('EmotionLog', backref='user', lazy=True)
    preferences = db.relationship('UserPreferences', backref='user', uselist=False, lazy=True)  # Added

# ... (PredictionHistory, EmotionLog, DailyPlan, UserPreferences unchanged) ...

class PredictionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prediction = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    glucose = db.Column(db.Float)
    bp = db.Column(db.Float)
    bmi = db.Column(db.Float)
    age = db.Column(db.Integer)

class EmotionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class DailyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    morning = db.Column(db.String(200))
    lunch = db.Column(db.String(200))
    evening = db.Column(db.String(200))
    dinner = db.Column(db.String(200))
    juice = db.Column(db.String(200))

class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dietary_preference = db.Column(db.String(50))
    allergies = db.Column(db.String(200))

