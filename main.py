# main.py (Nihai ve Düzeltilmiş Sürüm - Cache Kaldırıldı)
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_babel import _
from flask_login import login_required, current_user
from models import db, MasterRecord, UserList
from sqlalchemy import case, func
# from extensions import cache # Kaldırıldı

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.search_page'))

@main_bp.route('/my-list')
@login_required
def my_list():
    user_list_items_tuples = db.session.query(UserList, MasterRecord).join(MasterRecord).filter(UserList.user_id == current_user.id).all()
    
    all_tags, all_themes, all_demographics, years, studios = set(), set(), set(), set(), set()

    for user_list_obj, record_obj in user_list_items_tuples:
        if record_obj and record_obj.tags:
            for tag in record_obj.tags.split(','): all_tags.add(tag.strip())
        if record_obj and record_obj.themes:
            for theme in record_obj.themes.split(','): all_themes.add(theme.strip())
        if record_obj and record_obj.demographics:
            for demo in record_obj.demographics.split(','): all_demographics.add(demo.strip())
        if record_obj and record_obj.release_year:
            years.add(record_obj.release_year)
        if record_obj and record_obj.studios:
            studios.add(record_obj.studios)

    user_list = [{'list_item': user_list_obj, 'record': record_obj} for user_list_obj, record_obj in user_list_items_tuples]
    
    return render_template(
        'dashboard.html', title=_('Listem'), user_list=user_list,
        tags=sorted(list(all_tags)),
        themes=sorted(list(all_themes)),
        demographics=sorted(list(all_demographics)),
        years=sorted(list(years), reverse=True),
        studios=sorted(list(studios))
    )

@main_bp.route('/search')
# @cache.cached(timeout=3600) # Kaldırıldı
def search_page():
    studios = db.session.query(MasterRecord.studios).filter(MasterRecord.studios.isnot(None)).distinct().order_by(MasterRecord.studios).all()
    studios = [s[0] for s in studios if s[0]]
    
    tags_query = db.session.query(MasterRecord.tags).filter(MasterRecord.tags.isnot(None)).all()
    all_tags = set()
    for row in tags_query:
        if row[0]:
            for tag in row[0].split(','): all_tags.add(tag.strip())
    
    themes_query = db.session.query(MasterRecord.themes).filter(MasterRecord.themes.isnot(None)).all()
    all_themes = set()
    for row in themes_query:
        if row[0]:
            for tag in row[0].split(','): all_themes.add(tag.strip())
    
    demos_query = db.session.query(MasterRecord.demographics).filter(MasterRecord.demographics.isnot(None)).all()
    all_demos = set()
    for row in demos_query:
        if row[0]:
            for tag in row[0].split(','): all_demos.add(tag.strip())
            
    years = db.session.query(MasterRecord.release_year).filter(MasterRecord.release_year.isnot(None)).distinct().order_by(MasterRecord.release_year.desc()).all()
    years = [y[0] for y in years if y[0]]
    
    return render_template('search.html', title=_('Arama'), studios=studios, tags=sorted(list(all_tags)), themes=sorted(list(all_themes)), demographics=sorted(list(all_demos)), years=years)

@main_bp.route('/top')
# @cache.cached(timeout=3600) # Kaldırıldı
def top_records():
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

    return render_template('top_records.html', title=_('En İyiler'), top_list=top_list_query)

# --- API Endpoints (değişiklik yok) ---
@main_bp.route('/api/advanced-search')
def advanced_search():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = request.args.get('q', '', type=str)
    tags = request.args.get('tags', '', type=str)
    themes = request.args.get('themes', '', type=str)
    demos = request.args.get('demographics', '', type=str)
    year = request.args.get('year', '', type=str)
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
    if themes:
        theme_list = [f"%{t.strip()}%" for t in themes.split(',')]
        for t in theme_list:
            base_query = base_query.filter(MasterRecord.themes.ilike(t))
    if demos:
        demo_list = [f"%{d.strip()}%" for d in demos.split(',')]
        for d in demo_list:
            base_query = base_query.filter(MasterRecord.demographics.ilike(d))
    if studio:
        base_query = base_query.filter(MasterRecord.studios == studio)
    if year:
        try:
            year_int = int(year)
            base_query = base_query.filter(MasterRecord.release_year == year_int)
        except ValueError:
            pass
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
        'id': record.id,
        'title': record.original_title,
        'image': record.image_url,
        'type': record.mal_type,
        'record_type': record.record_type,
        'synopsis': record.synopsis,
        'score': record.score,
        'status': record.status,
        'release_year': record.release_year,
        'total_episodes': record.total_episodes,
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
    if item.user_id != current_user.id: return jsonify({'success': False, 'message': _('Yetkisiz işlem.')}), 403
    data = request.get_json()
    item.status = data.get('status', item.status)
    requested_chapter = data.get('current_chapter', item.current_chapter)
    try:
        requested_chapter = int(requested_chapter)
    except Exception:
        requested_chapter = item.current_chapter
    total_eps = item.record.total_episodes or 0
    if total_eps and requested_chapter > total_eps:
        requested_chapter = total_eps
    if requested_chapter < 0:
        requested_chapter = 0
    item.current_chapter = requested_chapter
    item.user_score = data.get('user_score', item.user_score)
    item.notes = data.get('notes', item.notes)
    db.session.commit()
    if not data.get('silent'):
        flash(_("Kayıt başarıyla güncellendi!"), "success")
    return jsonify({'success': True})
@main_bp.route('/list/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_list(record_id):
    existing_entry = UserList.query.filter_by(user_id=current_user.id, master_record_id=record_id).first()
    if existing_entry: return jsonify({'success': False, 'message': _('Bu kayıt zaten listenizde.')}), 409
    master_record = MasterRecord.query.get(record_id)
    if not master_record: return jsonify({'success': False, 'message': _('Kayıt bulunamadı.')}), 404
    new_list_item = UserList(user_id=current_user.id, master_record_id=record_id, status='Planlandı')
    db.session.add(new_list_item)
    db.session.commit()
    return jsonify({'success': True, 'message': _("'%(title)s' başarıyla listenize eklendi!", title=master_record.original_title)})
@main_bp.route('/list/delete/<int:user_list_id>', methods=['POST'])
@login_required
def delete_list_item(user_list_id):
    item = UserList.query.get_or_404(user_list_id)
    if item.user_id != current_user.id: return jsonify({'success': False, 'message': _('Yetkisiz işlem.')}), 403
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': _("Kayıt listenizden başarıyla kaldırıldı.")})
@main_bp.route('/api/record/<int:record_id>')
def get_record_details(record_id):
    record = MasterRecord.query.get_or_404(record_id)
    return jsonify({
        'id': record.id,
        'original_title': record.original_title,
        'english_title': record.english_title,
        'image_url': record.image_url,
        'synopsis': record.synopsis,
        'release_year': record.release_year,
        'source': record.source,
        'studios': record.studios,
        'demographics': record.demographics,
        'themes': record.themes,
        'tags': record.tags,
        'record_type': record.record_type,
        'mal_type': record.mal_type,
        'total_episodes': record.total_episodes,
        'score': record.score,
        'status': record.status
    })
@main_bp.route('/language/<lang>')
def set_language(lang=None):
    from flask import session
    if lang in ['tr', 'en']:
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))