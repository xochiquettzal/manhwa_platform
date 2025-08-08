# main.py (Nihai ve Düzeltilmiş Sürüm)

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, MasterRecord, UserList
from sqlalchemy import case, func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Ana sayfa artık Top listesine yönlendiriyor
    return redirect(url_for('main.top_records'))

@main_bp.route('/my-list')
@login_required
def my_list():
    """Kullanıcının ana paneli - My List sayfası."""
    # Bu sorgu bir demet listesi döndürür: [(UserList_obj, MasterRecord_obj), ...]
    user_list_items_tuples = db.session.query(UserList, MasterRecord).join(MasterRecord).filter(UserList.user_id == current_user.id).all()
    
    # Tüm etiketleri toplayıp filtreleme için hazırlama
    all_tags = set()
    # DÖNGÜ DÜZELTMESİ: Demeti doğrudan "açıyoruz" (unpacking)
    for user_list_obj, record_obj in user_list_items_tuples:
        if record_obj and record_obj.tags:
            for tag in record_obj.tags.split(','):
                all_tags.add(tag.strip())
    
    # Şablona göndereceğimiz veriyi oluşturuyoruz
    user_list = [
        {'list_item': user_list_obj, 'record': record_obj} 
        for user_list_obj, record_obj in user_list_items_tuples
    ]
    return render_template('dashboard.html', title='Listem', user_list=user_list, tags=sorted(list(all_tags)))

@main_bp.route('/search')
def search_page():
    """Gelişmiş arama sayfasını render eder."""
    studios = db.session.query(MasterRecord.studios).filter(MasterRecord.studios.isnot(None)).distinct().order_by(MasterRecord.studios).all()
    studios = [s[0] for s in studios if s[0]]
    
    tags_query = db.session.query(MasterRecord.tags).filter(MasterRecord.tags.isnot(None)).all()
    all_tags = set()
    for row in tags_query:
        if row[0]:
            for tag in row[0].split(','):
                all_tags.add(tag.strip())

    return render_template('search.html', title='Arama', studios=studios, tags=sorted(list(all_tags)))

@main_bp.route('/top')
def top_records():
    """Weighted Score'a göre sıralanmış Top listesini gösterir."""
    m = 1000 
    C = db.session.query(func.avg(MasterRecord.score)).filter(MasterRecord.score.isnot(None)).scalar() or 7.0
    
    weighted_score_formula = (
        (MasterRecord.scored_by / (MasterRecord.scored_by + m)) * MasterRecord.score +
        (m / (MasterRecord.scored_by + m)) * C
    ).label('weighted_score')

    top_list_query = db.session.query(MasterRecord, weighted_score_formula).filter(
        MasterRecord.scored_by >= m,
        MasterRecord.score.isnot(None)
    ).order_by(
        weighted_score_formula.desc()
    ).limit(50).all()
    
    return render_template('top_records.html', title='En İyiler', top_list=top_list_query)

# --- API Endpoints ---

@main_bp.route('/api/advanced-search')
def advanced_search():
    """Gelişmiş arama ve sonsuz kaydırma için API."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = request.args.get('q', '', type=str)
    tags = request.args.get('tags', '', type=str)
    studio = request.args.get('studio', '', type=str)
    sort_by = request.args.get('sort_by', 'popularity', type=str)
    
    base_query = MasterRecord.query

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(db.or_(MasterRecord.original_title.ilike(search_term), MasterRecord.english_title.ilike(search_term)))
    
    if tags:
        tag_list = [f"%{tag.strip()}%" for tag in tags.split(',')]
        for tag in tag_list:
            base_query = base_query.filter(MasterRecord.tags.ilike(tag))
            
    if studio:
        base_query = base_query.filter(MasterRecord.studios == studio)
        
    if sort_by == 'score':
        base_query = base_query.order_by(MasterRecord.score.desc().nullslast())
    else:
        base_query = base_query.order_by(MasterRecord.popularity.asc().nullslast())

    pagination = base_query.paginate(page=page, per_page=per_page, error_out=False)
    results = pagination.items
    
    user_list_record_ids = set()
    if current_user.is_authenticated:
        user_list_record_ids = {item.master_record_id for item in current_user.list_items}

    results_dict = [{
        'id': record.id, 'title': record.original_title, 'image': record.image_url, 
        'type': record.mal_type, 'synopsis': record.synopsis, 'score': record.score,
        'in_list': record.id in user_list_record_ids
    } for record in results]
    
    return jsonify({
        'results': results_dict,
        'has_next': pagination.has_next
    })


@main_bp.route('/list/update/<int:user_list_id>', methods=['POST'])
@login_required
def update_list_item(user_list_id):
    item = UserList.query.get_or_404(user_list_id)
    if item.user_id != current_user.id: return jsonify({'success': False, 'message': 'Yetkisiz işlem.'}), 403
    data = request.get_json()
    item.status = data.get('status', item.status)
    item.current_chapter = data.get('current_chapter', item.current_chapter)
    item.user_score = data.get('user_score', item.user_score)
    item.notes = data.get('notes', item.notes)
    db.session.commit()
    flash("Kayıt başarıyla güncellendi!", "success")
    return jsonify({'success': True})

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
    return jsonify({'success': True, 'message': f"'{master_record.original_title}' başarıyla listenize eklendi!"})

@main_bp.route('/list/delete/<int:user_list_id>', methods=['POST'])
@login_required
def delete_list_item(user_list_id):
    item = UserList.query.get_or_404(user_list_id)
    if item.user_id != current_user.id: return jsonify({'success': False, 'message': 'Yetkisiz işlem.'}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': "Kayıt listenizden başarıyla kaldırıldı."})