from flask import Blueprint, render_template, redirect, url_for, flash, request
from models import db, User
from forms import LoginForm, RegistrationForm
from utils import send_email, generate_confirmation_token, confirm_token
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    # validate_on_submit(), formdaki tüm temel ve özel doğrulamaları çalıştırır.
    # Eğer herhangi bir doğrulama (bizim yazdıklarımız dahil) başarısız olursa,
    # bu blok 'False' döner ve form, hatalarla birlikte tekrar render edilir.
    if form.validate_on_submit():
        # Bu bloğa sadece TÜM doğrulamalar başarılıysa girilir.
        user = User(
            username=form.username.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        token = generate_confirmation_token(user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('auth/confirm_email.html', confirm_url=confirm_url, user=user)
        send_email(user.email, 'Lütfen E-postanızı Onaylayın', html)

        flash('Onay linki e-posta adresinize gönderildi.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Kayıt Ol', form=form)

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('Onay linki geçersiz veya süresi dolmuş.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Hesap zaten onaylanmış. Lütfen giriş yapın.', 'success')
    else:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        login_user(user) # Onayladıktan sonra otomatik giriş yap
        flash('Hesabınızı onayladığınız için teşekkürler! Hoş geldiniz!', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Geçersiz e-posta veya şifre.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.confirmed:
            flash('Lütfen giriş yapmadan önce e-posta adresinizi onaylayın.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.index'))
        
    return render_template('auth/login.html', title='Giriş Yap', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))