from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# UserList (Kullanıcıların kişisel listelerini tutan ilişki tablosu)
class UserList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    master_record_id = db.Column(db.Integer, db.ForeignKey('master_record.id'), nullable=False)
    
    # Kullanıcıya özel veriler
    status = db.Column(db.String(50), default='Planlandı')
    current_chapter = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    # İlişkiyi kolayca sorgulamak için (bir liste öğesinin ana kaydına erişim)
    record = db.relationship('MasterRecord')

# User (Kullanıcı Tablosu)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Bir kullanıcının listesindeki tüm kayıtları kolayca çekmek için
    list_items = db.relationship('UserList', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# MasterRecord (Admin tarafından eklenen ana kütüphane tablosu)
class MasterRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_title = db.Column(db.String(200), nullable=False, unique=True)
    english_title = db.Column(db.String(200)) # Opsiyonel
    record_type = db.Column(db.String(50), default='Manhwa') # Manhwa, Anime, etc.
    image_url = db.Column(db.String(255))

    def __repr__(self):
        return f'<MasterRecord {self.original_title}>'