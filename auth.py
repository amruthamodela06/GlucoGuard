from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']  # Add this line
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Try logging in.', 'warning')
            return redirect('/login')

        new_user = User(username=username, name=name, email=email, password=password)  # Add username here
        db.session.add(new_user)
        db.session.commit()
        flash('Successfully signed up! Please log in.', 'success')
        return redirect('/login')
    return render_template('signup.html', hide_navbar=True)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['name'] = user.name
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid email or password.', 'danger')
            return redirect('/login')
    return render_template('login.html', hide_navbar=True)

@auth.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect('/')

