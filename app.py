import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from models import db

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

# --- UYGULAMA KURULUMU ---
# Eklentileri global olarak başlatıyoruz
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app():
    """Uygulama fabrikası fonksiyonu."""
    app = Flask(__name__)

    # --- KONFİGÜRASYON ---
    # Veritabanı konumu
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
    # Flask ve eklentileri için gizli anahtar
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-super-secret-key-change-it')
    
    # --- E-POSTA KONFİGÜRASYONU (.env dosyasından okunacak) ---
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # --- EKLENTİLERİ UYGULAMA İLE BAĞLAMA ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Login yöneticisi için giriş sayfasını ve mesaj kategorisini belirt
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # --- USER LOADER FONKSİYONU ---
    # Bu fonksiyon, kullanıcı oturumunu yönetmek için gereklidir.
    # Döngüsel import hatalarını önlemek için burada tanımlanır.
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- BLUEPRINT'LERİ KAYDETME ---
    # Uygulamanın farklı bölümlerini (auth, main) kaydet
    with app.app_context():
        from auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from main import main_bp
        app.register_blueprint(main_bp)

        from admin import admin_bp
        app.register_blueprint(admin_bp)

    return app

# Uygulamayı doğrudan çalıştırmak için (geliştirme sırasında)
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)