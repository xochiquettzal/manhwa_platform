# app.py (Final Sürümü - Cache ve Limiter ile)
import os
from flask import Flask, send_from_directory, request, session, redirect, url_for
from flask_babel import get_locale
from extensions import db, migrate, login_manager, mail, babel, cache, limiter # limiter eklendi
from models import User
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-super-secret-key-change-it')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['LANGUAGES'] = ['en', 'tr']
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 3600

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app) # Limiter başlatıldı

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
        # Auth endpointlerine daha katı limitler
        limiter.limit("15 per minute")(auth_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        from admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        from main import main_bp
        # API endpointlerine daha esnek limitler
        limiter.limit("120 per minute", methods=["GET"])(main_bp) # Arama gibi GET istekleri
        limiter.limit("60 per minute", methods=["POST"])(main_bp) # Ekleme/silme gibi POST istekleri
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