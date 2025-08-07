# admin.py (Zengin Veri Alanları Eklenmiş Final Hali)

import os
import json
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
    return jsonify({
        'id': record.id, 'original_title': record.original_title, 'english_title': record.english_title,
        'record_type': record.record_type, 'image_url': record.image_url, 'synopsis': record.synopsis,
        'tags': record.tags, 'source': record.source, 'studios': record.studios,
        'release_year': record.release_year, 'total_episodes': record.total_episodes
    })

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
    new_record = MasterRecord(
        original_title=request.form['original_title'],
        english_title=request.form.get('english_title', ''),
        record_type=request.form.get('record_type', 'Manhwa'),
        image_url=image_path,
        synopsis=request.form.get('synopsis', ''),
        tags=request.form.get('tags', ''),
        source=request.form.get('source', ''),
        studios=request.form.get('studios', ''),
        release_year=request.form.get('release_year', None, type=int),
        total_episodes=request.form.get('total_episodes', None, type=int)
    )
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
    record.synopsis = request.form.get('synopsis', '')
    record.image_url = image_path
    record.tags = request.form.get('tags', '')
    record.source = request.form.get('source', '')
    record.studios = request.form.get('studios', '')
    record.release_year = request.form.get('release_year', None, type=int)
    record.total_episodes = request.form.get('total_episodes', None, type=int)

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

@admin_bp.route('/api/bulk-import', methods=['POST'])
@login_required
@admin_required
def bulk_import():
    if 'import_file' not in request.files: return jsonify({'message': 'Dosya bulunamadı.'}), 400
    file = request.files['import_file']
    if file.filename == '' or not file.filename.endswith('.json'): return jsonify({'message': 'Lütfen geçerli bir .json dosyası seçin.'}), 400
    
    added_count = 0
    skipped_count = 0
    try:
        data = json.load(file)
        if not isinstance(data, list): raise ValueError("JSON dosyası bir liste (array) içermelidir.")
        
        existing_titles = {record.original_title for record in MasterRecord.query.all()}
        for item in data:
            title = item.get('original_title')
            if not isinstance(title, str) or not title or title in existing_titles:
                skipped_count += 1
                continue

            new_record = MasterRecord(
                original_title=title,
                english_title=item.get('english_title'),
                record_type=item.get('record_type', 'Manhwa'),
                image_url=item.get('image_url'),
                synopsis=item.get('synopsis'),
                tags=item.get('tags'),
                source=item.get('source'),
                studios=item.get('studios'),
                release_year=item.get('release_year'),
                total_episodes=item.get('total_episodes')
            )
            db.session.add(new_record)
            existing_titles.add(title)
            added_count += 1
        
        db.session.commit()
        message = f"{added_count} kayıt başarıyla eklendi. {skipped_count} kayıt (mevcut veya başlık eksik) atlandı."
        return jsonify({'message': message})

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f"Bir hata oluştu: {str(e)}"}), 500