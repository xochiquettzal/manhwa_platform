# extensions.py (Final Sürümü)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel
from flask_caching import Cache
from flask_limiter import Limiter             # Eklendi
from flask_limiter.util import get_remote_address # Eklendi

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
babel = Babel()
cache = Cache()
# Limiter'ı IP adresine göre çalışacak şekilde ayarla
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]) # Eklendi