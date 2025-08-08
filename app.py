# app.py (Final Sürümü)

import os
from flask import Flask, send_from_directory, request, session, redirect, url_for
from flask_babel import get_locale
from extensions import db, migrate, login_manager, mail, babel
from models import User
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    # Render PostgreSQL için DATABASE_URL ortam değişkenini kullan,
    # yoksa yerel geliştirme için sqlite kullan.
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///platform.db'
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-super-secret-key-change-it')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['LANGUAGES'] = ['en', 'tr']
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    def locale_selector():
        if 'language' in session and session['language'] in app.config['LANGUAGES']:
            return session.get('language')
        return request.accept_languages.best_match(app.config['LANGUAGES'])

    babel.init_app(app, locale_selector=locale_selector)

    @app.context_processor
    def inject_locale():
        return dict(get_locale=get_locale)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        from auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        from admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        from main import main_bp
        app.register_blueprint(main_bp)



    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        upload_folder_path = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder_path):
            os.makedirs(upload_folder_path)
    app.run(debug=True)

# Gunicorn'un kullanması için app nesnesini oluştur
app = create_app()