from flask import Blueprint, render_template, redirect, url_for, request, flash
from Models.models import db, login_manager, User, UserDynamic
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        username2 = request.form['username2']
        email = request.form['email']
        userkind = request.form['userkind']
        if not username or not password or not username2 or not email or not userkind:
            flash('All fields are required!')
        elif User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists!')
        else:
            user = User(username=username, password=password, username2=username2, email=email, userkind=userkind)
            db.session.add(user)
            db.session.commit()
            user_dynamic = UserDynamic(user_id=user.id)
            db.session.add(user_dynamic)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            user_dynamic = UserDynamic.query.filter_by(user_id=user.id).first()
            user_dynamic.last_login_time = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
