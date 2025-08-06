# main.py (index fonksiyonunun yeni hali)

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, MasterRecord, UserList

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Kullanıcının ana panelini ve kişisel listesini gösterir."""
    user_list_items = UserList.query.filter_by(user_id=current_user.id).order_by(UserList.id.desc()).all()
    return render_template('dashboard.html', title="Panelim", user_list=user_list_items)
    
@main_bp.route('/api/search')
@login_required
def search_master_records():
    """MasterRecord kütüphanesinde canlı arama yapar."""
    query = request.args.get('q', '').strip()
    if len(query) < 2: # Çok kısa sorguları çalıştırma
        return jsonify([])

    # Hem orijinal hem de İngilizce başlıkta arama yap (büyük/küçük harf duyarsız)
    search_term = f"%{query}%"
    results = MasterRecord.query.filter(
        db.or_(
            MasterRecord.original_title.ilike(search_term),
            MasterRecord.english_title.ilike(search_term)
        )
    ).limit(10).all() # Çok fazla sonuç dönmemesi için limit koy

    # Sonuçları JSON formatına uygun hale getir
    results_dict = [
        {
            'id': record.id, 
            'original_title': record.original_title,
            'image_url': record.image_url or 'https://via.placeholder.com/40x56.png?text=N/A'
        } 
        for record in results
    ]
    return jsonify(results_dict)

@main_bp.route('/list/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_list(record_id):
    """Bir kaydı kullanıcının kişisel listesine ekler."""
    # Kayıt zaten bu kullanıcının listesinde var mı diye kontrol et
    existing_entry = UserList.query.filter_by(
        user_id=current_user.id, 
        master_record_id=record_id
    ).first()

    if existing_entry:
        return jsonify({'success': False, 'message': 'Bu kayıt zaten listenizde mevcut.'}), 409 # 409 Conflict

    # MasterRecord var mı diye kontrol et
    master_record = MasterRecord.query.get(record_id)
    if not master_record:
        return jsonify({'success': False, 'message': 'Ana kayıt bulunamadı.'}), 404 # 404 Not Found

    # Yeni liste öğesini oluştur ve veritabanına ekle
    new_list_item = UserList(
        user_id=current_user.id,
        master_record_id=record_id,
        status='Planlandı' # Varsayılan durum
    )
    db.session.add(new_list_item)
    db.session.commit()
    
    # Başarı mesajını flash ile gönderebiliriz, ama en basiti sayfayı yenilemek olacak.
    # Frontend bu cevaba göre sayfayı yenileyecek.
    return jsonify({'success': True, 'message': 'Kayıt başarıyla eklendi.'})