# utils.py (Nihai Sürüm)
from functools import wraps
from flask import flash, redirect, url_for, current_app, render_template
from flask_login import current_user
from flask_mail import Message
from extensions import mail
from itsdangerous import URLSafeTimedSerializer
from models import User # User modeli eklendi

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Bu sayfaya erişim yetkiniz yok.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def send_email(to, subject, template):
    msg = Message(subject, recipients=[to], html=template, sender=current_app.config['MAIL_DEFAULT_SENDER'])
    mail.send(msg)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirmation-salt')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirmation-salt', max_age=expiration)
    except:
        return False
    return email

# YENİ EKLENDİ
def generate_password_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

# YENİ EKLENDİ
def confirm_password_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        user = User.query.filter_by(email=email).first()
        if user:
            return user
    except:
        return None
    return None