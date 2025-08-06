from flask_mail import Message
from app import mail
from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer

def send_email(to, subject, template):
    """Genel e-posta gönderme fonksiyonu."""
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

def generate_confirmation_token(email):
    """E-posta onayı için güvenli bir token oluşturur."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirmation-salt')

def confirm_token(token, expiration=3600):
    """Verilen token'ı doğrular. Süresi dolmuşsa (1 saat) False döner."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirmation-salt',
            max_age=expiration
        )
    except:
        return False
    return email