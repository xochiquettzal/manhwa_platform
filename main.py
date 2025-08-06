# main.py (Son Hali)

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, MasterRecord, UserList

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Kullanıcının ana panelini ve kişisel listesini gösterir."""
    user_list_items = db.session.query(UserList, MasterRecord).join(MasterRecord).filter(UserList.user_id == current_user.id).all()
    user_list = [
        {'list_item': item.UserList, 'record': item.MasterRecord} 
        for item in user_list_items
    ]
    return render_template('dashboard.html', title='Panelim', user_list=user_list)

@main_bp.route('/api/search')
@login_required
def search():
    """MasterRecord kütüphanesinde arama yapar ve JSON sonucu döndürür."""
    query = request.args.get('q', '', type=str)
    if len(query) < 3: return jsonify([])

    search_term = f"%{query}%"
    user_list_ids = [item.master_record_id for item in current_user.list_items]
    results = MasterRecord.query.filter(
        db.or_(
            MasterRecord.original_title.ilike(search_term),
            MasterRecord.english_title.ilike(search_term)
        ),
        MasterRecord.id.notin_(user_list_ids)
    ).limit(10).all()

    results_dict = [{'id': record.id, 'title': record.original_title, 'image': record.image_url} for record in results]
    return jsonify(results_dict)

@main_bp.route('/list/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_list(record_id):
    """Bir kaydı kullanıcının kişisel listesine ekler."""
    existing_entry = UserList.query.filter_by(user_id=current_user.id, master_record_id=record_id).first()
    if existing_entry: return jsonify({'success': False, 'message': 'Bu kayıt zaten listenizde.'}), 409

    master_record = MasterRecord.query.get(record_id)
    if not master_record: return jsonify({'success': False, 'message': 'Kayıt bulunamadı.'}), 404

    new_list_item = UserList(user_id=current_user.id, master_record_id=record_id, status='Planlandı')
    db.session.add(new_list_item)
    db.session.commit()
    
    flash(f"'{master_record.original_title}' başarıyla listenize eklendi!", "success")
    return jsonify({'success': True})

@main_bp.route('/list/update/<int:user_list_id>', methods=['POST'])
@login_required
def update_list_item(user_list_id):
    """Kullanıcının listesindeki bir öğeyi günceller."""
    item = UserList.query.get_or_404(user_list_id)
    
    if item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Yetkisiz işlem.'}), 403
    
    data = request.get_json()
    item.status = data.get('status', item.status)
    item.current_chapter = data.get('current_chapter', item.current_chapter)
    item.notes = data.get('notes', item.notes) # Notları güncelle
    
    db.session.commit()
    flash("Kayıt başarıyla güncellendi!", "success")
    return jsonify({'success': True})