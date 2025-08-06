# extensions.py (Babel Eklenmiş Hali)

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel # Bu satırı ekliyoruz

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
babel = Babel() # Babel nesnesini burada başlatıyoruz