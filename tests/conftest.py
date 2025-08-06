# tests/conftest.py (Final Hali)

import pytest
from app import create_app, db
from models import User

@pytest.fixture(scope='function') # Değişiklik: module -> function
def new_user():
    """Her test için yeni bir kullanıcı nesnesi oluşturur."""
    user = User(username='testuser', email='test@example.com', confirmed=True)
    user.set_password('password123')
    return user

@pytest.fixture(scope='function') # Değişiklik: module -> function
def new_admin():
    """Her test için yeni bir admin nesnesi oluşturur."""
    admin = User(username='adminuser', email='admin@example.com', confirmed=True, is_admin=True)
    admin.set_password('password123')
    return admin

@pytest.fixture(scope='session')
def app():
    """Tüm testler için tek bir Flask uygulaması oluşturur."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False,
        # E-posta göndermeyi devre dışı bırakarak testleri hızlandır
        "MAIL_SUPPRESS_SEND": True, 
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function') # Değişiklik: Her test için temiz veritabanı
def client(app):
    """Her test fonksiyonu için bir test istemcisi ve temiz bir veritabanı."""
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client