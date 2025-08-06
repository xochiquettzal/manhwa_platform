# admin.py (Final Sürümü)

import os
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from models import db, MasterRecord
from utils import admin_required

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file(filename): return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html', title="Admin Paneli")

@admin_bp.route('/api/records')
@login_required
@admin_required
def get_records():
    query = request.args.get('q', '', type=str)
    if query:
        search_term = f"%{query}%"
        records = MasterRecord.query.filter(db.or_(MasterRecord.original_title.ilike(search_term), MasterRecord.english_title.ilike(search_term))).order_by(MasterRecord.original_title).all()
    else:
        records = MasterRecord.query.order_by(MasterRecord.original_title).all()
    return jsonify([{'id': r.id, 'title': r.original_title, 'image': r.image_url} for r in records])

@admin_bp.route('/api/record/<int:record_id>')
@login_required
@admin_required
def get_record(record_id):
    record = MasterRecord.query.get_or_404(record_id)
    return jsonify({'id': record.id, 'original_title': record.original_title, 'english_title': record.english_title, 'record_type': record.record_type, 'image_url': record.image_url})

@admin_bp.route('/api/record/add', methods=['POST'])
@login_required
@admin_required
def add_record():
    if 'original_title' not in request.form or not request.form['original_title']: return jsonify({'message': 'Orijinal başlık zorunludur.'}), 400
    image_path = request.form.get('image_url', '')
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image_path = f"/uploads/{filename}"
    new_record = MasterRecord(original_title=request.form['original_title'], english_title=request.form.get('english_title', ''), record_type=request.form.get('record_type', 'Manhwa'), image_url=image_path)
    db.session.add(new_record)
    db.session.commit()
    return jsonify({'message': 'Kayıt başarıyla eklendi.'}), 201

@admin_bp.route('/api/record/update/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def update_record(record_id):
    record = MasterRecord.query.get_or_404(record_id)
    image_path = record.image_url
    if request.form.get('image_url'): image_path = request.form.get('image_url')
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image_path = f"/uploads/{filename}"
    record.original_title = request.form['original_title']
    record.english_title = request.form.get('english_title', '')
    record.record_type = request.form.get('record_type', 'Manhwa')
    record.image_url = image_path
    db.session.commit()
    return jsonify({'message': 'Kayıt başarıyla güncellendi.'})

@admin_bp.route('/api/record/delete/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def delete_record(record_id):
    record = MasterRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': 'Kayıt başarıyla silindi.'})