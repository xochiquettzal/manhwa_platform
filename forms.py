# forms.py (Tam Hali)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    # Madde 5: E-posta alanı, artık hem e-posta hem de kullanıcı adı kabul edecek şekilde değiştirildi.
    login = StringField('E-posta veya Kullanıcı Adı', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember_me = BooleanField('Beni hatırla')
    # Submit butonu artık HTML'de tanımlanacak.

class RegistrationForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Şifreyi Doğrula', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor.')])
    # Submit butonu artık HTML'de tanımlanacak.

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Bu kullanıcı adı alınmış. Lütfen farklı bir tane seçin.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu e-posta adresi zaten kullanılıyor.')

class MasterRecordForm(FlaskForm):
    original_title = StringField('Orijinal Başlık', validators=[DataRequired()])
    english_title = StringField('İngilizce Başlık (Opsiyonel)')
    record_type = SelectField('Tür', choices=[
        ('Manhwa', 'Manhwa'), 
        ('Anime', 'Anime'), 
        ('Manga', 'Manga'), 
        ('Webtoon', 'Webtoon')
    ], validators=[DataRequired()])
    image_url = StringField('Kapak Fotoğrafı URL')
    submit = SubmitField('Kaydı Ekle')