# app.py (Final Sürümü)

import os
from flask import Flask, send_from_directory
from extensions import db, migrate, login_manager, mail
from models import User
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """Uygulama fabrikası fonksiyonu."""
    app = Flask(__name__)

    # --- KONFİGÜRASYON ---
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-super-secret-key-change-it')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # --- E-POSTA KONFİGÜRASYONU ---
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # --- EKLENTİLERİ BAŞLATMA ---
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # --- LOGIN MANAGER YAPILANDIRMASI ---
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None # Giriş yap uyarısını kaldır

    # --- USER LOADER ---
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- BLUEPRINT'LERİ (UYGULAMA BÖLÜMLERİNİ) KAYDETME ---
    with app.app_context():
        from auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        from main import main_bp
        app.register_blueprint(main_bp)

    # --- YÜKLENEN DOSYALAR İÇİN ROUTE ---
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app

# Uygulamayı `python app.py` ile doğrudan çalıştırmak için
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        upload_folder_path = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder_path):
            os.makedirs(upload_folder_path)
    app.run(debug=True)