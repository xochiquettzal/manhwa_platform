# app.py (Refactored with Configuration and Logging)
import os
from flask import Flask, send_from_directory, request, session, redirect, url_for, render_template
from flask_babel import get_locale
from extensions import db, migrate, login_manager, mail, babel, limiter
from models import User
from config import config
from logging_config import setup_logging
import logging

def create_app(config_name=None):
    """Application factory pattern"""
    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logging(app)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting application with {config_name} configuration")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Flask-Limiter disabled for better user experience
    # limiter.init_app(app)
    
    # Suppress Flask-Limiter warnings in development
    if app.config.get('DEBUG'):
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")
    
    # Setup internationalization
    setup_babel(app)
    
    # Setup authentication
    setup_auth(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup file upload route
    setup_file_uploads(app)
    
    logger.info("Application factory completed successfully")
    return app

def setup_babel(app):
    """Setup Babel internationalization"""
    def locale_selector():
        if 'language' in session and session['language'] in app.config['LANGUAGES']:
            return session.get('language')
        return request.accept_languages.best_match(app.config['LANGUAGES'])
    
    babel.init_app(app, locale_selector=locale_selector)
    
    @app.context_processor
    def inject_locale():
        return dict(get_locale=get_locale)

def setup_auth(app):
    """Setup authentication"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

def register_blueprints(app):
    """Register application blueprints"""
    with app.app_context():
        # Import blueprints
        from auth import auth_bp
        from admin import admin_bp
        from main import main_bp
        
        # Rate limiting disabled for better user experience
        # limiter.limit("15 per minute")(auth_bp)
        # limiter.limit("120 per minute", methods=["GET"])(main_bp)
        # limiter.limit("60 per minute", methods=["POST"])(main_bp)
        
        # Register blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(main_bp)

def setup_error_handlers(app):
    """Setup error handlers"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return render_template('errors/413.html'), 413

def setup_file_uploads(app):
    """Setup file upload handling"""
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure upload folder exists
    upload_folder_path = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_folder_path):
        os.makedirs(upload_folder_path)

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration
    host = app.config.get('HOST', '127.0.0.1')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    # Development'da debug mode'u kapat (duplicate logging'i önlemek için)
    if os.environ.get('FLASK_ENV') == 'development':
        debug = False

    
    try:
        # Debug mode'u kapatarak duplicate logging'i önle
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print(f"\n👋 Manhwa Platform kapatılıyor...")
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")