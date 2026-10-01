from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name  = request.form['name']
        email = request.form['email']
        pwd   = request.form['password']
        role  = request.form.get('role', 'customer')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))

        user = User(name=name, email=email, role=role)
        user.set_password(pwd)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful, please log in', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form['email']
        pwd   = request.form['password']
        user  = User.query.filter_by(email=email).first()

        if user and user.check_password(pwd):
            login_user(user)
            flash('Logged in successfully', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            if user.is_seller:
                return redirect(url_for('seller.dashboard'))
            else:
                return redirect(url_for('customer.catalog'))
        flash('Invalid email or password', 'danger')

    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('main.index'))