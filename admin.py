# admin.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, MasterRecord
from forms import MasterRecordForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin'e özel sayfalar için bir decorator (kontrol fonksiyonu)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Bu sayfaya erişim yetkiniz yok.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    records = MasterRecord.query.order_by(MasterRecord.original_title).all()
    return render_template('admin/dashboard.html', title="Admin Paneli", records=records)

@admin_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_record():
    form = MasterRecordForm()
    if form.validate_on_submit():
        new_record = MasterRecord(
            original_title=form.original_title.data,
            english_title=form.english_title.data,
            record_type=form.record_type.data,
            image_url=form.image_url.data
        )
        db.session.add(new_record)
        db.session.commit()
        flash(f"'{new_record.original_title}' başarıyla eklendi.", 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/add_record.html', title="Yeni Kayıt Ekle", form=form)