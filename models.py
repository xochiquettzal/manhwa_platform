# models.py (Nihai Sürüm - user_score alanı eklendi)

from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class UserList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    master_record_id = db.Column(db.Integer, db.ForeignKey('master_record.id'), nullable=False)
    status = db.Column(db.String(50), default='Planlandı')
    current_chapter = db.Column(db.Integer, default=0)
    user_score = db.Column(db.Integer, default=0) # YENİ: Kullanıcının 1-10 arası puanı (0 = Puanlanmamış)
    notes = db.Column(db.Text)
    record = db.relationship('MasterRecord')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    list_items = db.relationship('UserList', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MasterRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, unique=True, nullable=False)
    original_title = db.Column(db.String(200), nullable=False, unique=True)
    english_title = db.Column(db.String(200))
    record_type = db.Column(db.String(50), default='Manhwa')
    mal_type = db.Column(db.String(50))
    image_url = db.Column(db.String(255))
    synopsis = db.Column(db.Text)
    tags = db.Column(db.String(300))
    source = db.Column(db.String(50))
    studios = db.Column(db.String(150))
    release_year = db.Column(db.Integer)
    total_episodes = db.Column(db.Integer)
    score = db.Column(db.Float)
    popularity = db.Column(db.Integer)
    scored_by = db.Column(db.Integer)