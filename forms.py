# forms.py (Final Sürümü - lazy_gettext ile düzeltildi)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User
from flask_babel import lazy_gettext # _ yerine lazy_gettext import edildi

class LoginForm(FlaskForm):
    login = StringField(lazy_gettext('E-posta veya Kullanıcı Adı'), validators=[DataRequired()])
    password = PasswordField(lazy_gettext('Şifre'), validators=[DataRequired()])
    remember_me = BooleanField(lazy_gettext('Beni hatırla'))

class RegistrationForm(FlaskForm):
    username = StringField(lazy_gettext('Kullanıcı Adı'), validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField(lazy_gettext('E-posta'), validators=[DataRequired(), Email()])
    password = PasswordField(lazy_gettext('Şifre'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        lazy_gettext('Şifreyi Doğrula'), validators=[DataRequired(), EqualTo('password', message=lazy_gettext('Şifreler eşleşmiyor.'))])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(lazy_gettext('Bu kullanıcı adı alınmış. Lütfen farklı bir tane seçin.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(lazy_gettext('Bu e-posta adresi zaten kullanılıyor.'))

class RequestResetForm(FlaskForm):
    email = StringField(lazy_gettext('E-posta'), validators=[DataRequired(), Email()])

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError(lazy_gettext('Bu e-posta adresi ile kayıtlı bir hesap bulunamadı.'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(lazy_gettext('Yeni Şifre'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        lazy_gettext('Yeni Şifreyi Doğrula'), validators=[DataRequired(), EqualTo('password', message=lazy_gettext('Şifreler eşleşmiyor.'))])