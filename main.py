# main.py (Nihai Akıllı Sıralama ile Final Hali)

from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from models import db, MasterRecord, UserList
from sqlalchemy import case

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    user_list_items = db.session.query(UserList, MasterRecord).join(MasterRecord).filter(UserList.user_id == current_user.id).all()
    user_list = [{'list_item': item.UserList, 'record': item.MasterRecord} for item in user_list_items]
    return render_template('dashboard.html', title='Panelim', user_list=user_list)

@main_bp.route('/api/search')
@login_required
def search():
    query = request.args.get('q', '', type=str)
    if len(query) < 2: return jsonify([])
    search_term = f"%{query}%"
    user_list_ids = [item.master_record_id for item in current_user.list_items]
    
    # --- YENİ VE GELİŞMİŞ AKILLI SIRALAMA MANTIĞI ---
    # 1. mal_type'a göre bir öncelik puanı oluşturuyoruz.
    # Düşük puan, daha yüksek öncelik anlamına gelir.
    type_priority = case(
        (MasterRecord.mal_type == 'TV', 1),
        (MasterRecord.mal_type == 'Movie', 2),
        (MasterRecord.mal_type == 'Manga', 3), # Manga da yüksek öncelikli
        (MasterRecord.mal_type == 'Manhwa', 4),
        (MasterRecord.mal_type == 'Webtoon', 5),
        (MasterRecord.mal_type == 'OVA', 6),
        (MasterRecord.mal_type == 'ONA', 7),
        (MasterRecord.mal_type == 'Special', 8),
        else_=9 # Diğer her şey en sonda
    ).label('type_priority')

    results_query = MasterRecord.query.add_columns(type_priority).filter(
        db.or_(MasterRecord.original_title.ilike(search_term), MasterRecord.english_title.ilike(search_term)),
        MasterRecord.id.notin_(user_list_ids)
    ).order_by(
        # 2. Sonuçları bu önceliklere göre sıralıyoruz.
        MasterRecord.popularity, # ANA SIRALAMA: En popüler olan (en düşük sayı) en üste gelir.
        type_priority          # İKİNCİL SIRALAMA: Popülerlikleri aynıysa, tür önceliği devreye girer.
    ).limit(10).all()

    # Sonuçları dict'e çevirirken sadece MasterRecord'u al
    results_dict = [{'id': record.MasterRecord.id, 'title': record.MasterRecord.original_title, 'image': record.MasterRecord.image_url, 'type': record.MasterRecord.mal_type} for record in results_query]
    return jsonify(results_dict)

@main_bp.route('/list/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_list(record_id):
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
    item = UserList.query.get_or_404(user_list_id)
    if item.user_id != current_user.id: return jsonify({'success': False, 'message': 'Yetkisiz işlem.'}), 403
    data = request.get_json()
    item.status = data.get('status', item.status)
    item.current_chapter = data.get('current_chapter', item.current_chapter)
    item.notes = data.get('notes', item.notes)
    db.session.commit()
    flash("Kayıt başarıyla güncellendi!", "success")
    return jsonify({'success': True})

@main_bp.route('/list/delete/<int:user_list_id>', methods=['POST'])
@login_required
def delete_list_item(user_list_id):
    item = UserList.query.get_or_404(user_list_id)
    if item.user_id != current_user.id: return jsonify({'success': False, 'message': 'Yetkisiz işlem.'}), 403
    db.session.delete(item)
    db.session.commit()
    flash("Kayıt listenizden başarıyla kaldırıldı.", "success")
    return jsonify({'success': True})