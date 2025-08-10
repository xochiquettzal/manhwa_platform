# auth.py (Nihai Sürüm)
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_babel import _
from models import db, User
from forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm # Yeni formlar eklendi
from utils import send_email, generate_confirmation_token, confirm_token, generate_password_reset_token, confirm_password_reset_token # Yeni util'ler eklendi
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('auth/confirm_email.html', confirm_url=confirm_url, user=user)
        send_email(user.email, _('Lütfen E-postanızı Onaylayın'), html)
        flash(_('Onay linki e-posta adresinize gönderildi.'), 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Kayıt Ol'), form=form)

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    try: email = confirm_token(token)
    except:
        flash(_('Onay linki geçersiz veya süresi dolmuş.'), 'danger')
        return redirect(url_for('main.index'))
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash(_('Hesap zaten onaylanmış. Lütfen giriş yapın.'), 'success')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(_('Hesabınızı onayladığınız için teşekkürler! Hoş geldiniz!'), 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.email == form.login.data) | (User.username == form.login.data)).first()
        if user and user.check_password(form.password.data):
            if not user.confirmed:
                flash(_('Lütfen giriş yapmadan önce e-posta adresinizi onaylayın.'), 'warning')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash(_('Geçersiz E-posta/Kullanıcı Adı veya Şifre.'), 'danger')
    return render_template('auth/login.html', title=_('Giriş Yap'), form=form)

@auth_bp.route('/logout', methods=['POST']) # DEĞİŞİKLİK: methods=['POST'] eklendi
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def request_reset():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_password_reset_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            html = render_template('auth/reset_password_email.html', reset_url=reset_url, user=user)
            send_email(user.email, _('Şifre Sıfırlama İsteği'), html)
        flash(_('Şifre sıfırlama linki e-posta adresinize gönderildi.'), 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/request_reset.html', title=_('Şifre Sıfırla'), form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = confirm_password_reset_token(token)
    if user is None:
        flash(_('Şifre sıfırlama linki geçersiz veya süresi dolmuş.'), 'danger')
        return redirect(url_for('auth.request_reset'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Şifreniz başarıyla güncellendi! Giriş yapabilirsiniz.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', title=_('Yeni Şifre Belirle'), form=form)