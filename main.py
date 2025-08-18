# main.py (Nihai ve Düzeltilmiş Sürüm - Profil Sayfası ve Grafik Çevirisi ile)
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_babel import _
from flask_login import login_required, current_user
from models import db, MasterRecord, UserList
from sqlalchemy import case, func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.search_page'))

@main_bp.route('/my-list')
@login_required
def my_list():
    """Kullanıcının ana paneli - My List sayfası."""
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
def search_page():
    """Gelişmiş arama sayfasını render eder."""
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

    return render_template('top_records.html', title=_('En İyiler'), top_list=top_list_query)

@main_bp.route('/profile')
@login_required
def profile():
    """Kullanıcı profili ve istatistikleri sayfasını render eder."""
    
    # Veritabanından durum bazında sayıları çek (daha verimli)
    status_counts_query = db.session.query(UserList.status, func.count(UserList.id)).filter_by(user_id=current_user.id).group_by(UserList.status).all()
    
    # Ortalama puanı hesapla (0 olan puanları dahil etme)
    avg_score_query = db.session.query(func.avg(UserList.user_score)).filter(UserList.user_id == current_user.id, UserList.user_score > 0).scalar()
    
    # Toplam bölüm sayısını hesapla
    total_chapters_query = db.session.query(func.sum(UserList.current_chapter)).filter_by(user_id=current_user.id).scalar()

    # Sorgu sonuçlarını kolay kullanılabilir bir sözlüğe dönüştür
    status_counts = {status: count for status, count in status_counts_query}
    
    stats = {
        'total': sum(status_counts.values()),
        'watching': status_counts.get('İzleniyor', 0),
        'reading': status_counts.get('Okunuyor', 0),
        'completed': status_counts.get('Tamamlandı', 0),
        'planned': status_counts.get('Planlandı', 0),
        'dropped': status_counts.get('Bırakıldı', 0),
        'avg_score': f"{avg_score_query:.2f}" if avg_score_query else "N/A",
        'total_chapters': total_chapters_query or 0
    }

    # Pasta grafik için ham etiketleri ve verileri al
    chart_labels_raw = list(status_counts.keys())
    chart_data = list(status_counts.values())

    # Ham etiketleri _() fonksiyonu ile çevir
    translated_chart_labels = [_(label) for label in chart_labels_raw]

    return render_template('profile.html', 
                           title=_('Profilim'), 
                           stats=stats, 
                           chart_labels=translated_chart_labels, # Çevrilmiş listeyi gönder
                           chart_data=chart_data)

# --- API Endpoints ---
@main_bp.route('/api/advanced-search')
def advanced_search():
    """Gelişmiş arama ve sonsuz kaydırma için API."""
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
    """Search modalı için kayıt detaylarını döndürür."""
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
@main_bp.route('/import/mal', methods=['POST'])
@login_required
def import_mal_list():
    """MyAnimeList XML export dosyasını içe aktarır."""
    if 'mal_file' not in request.files:
        return jsonify({'success': False, 'message': _('Dosya yüklenmedi.')}), 400
    
    file = request.files['mal_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': _('Dosya seçilmedi.')}), 400
    
    if not file.filename.endswith('.xml'):
        return jsonify({'success': False, 'message': _('Sadece XML dosyaları desteklenir.')}), 400
    
    try:
        import xml.etree.ElementTree as ET
        import requests
        import time
        from datetime import datetime
        
        # XML'i parse et
        tree = ET.parse(file)
        root = tree.getroot()
        
        # MyAnimeList namespace'i
        namespace = {'mal': 'http://myanimelist.net/xsd/1.0'}
        
        # Kullanıcı bilgilerini al
        user_info = root.find('myinfo', namespace)
        if user_info is None:
            return jsonify({'success': False, 'message': _('Geçersiz MyAnimeList export dosyası.')}), 400
        
        # Anime listesini al
        anime_list = root.findall('anime', namespace)
        if not anime_list:
            return jsonify({'success': False, 'message': _('Anime listesi bulunamadı.')}), 400
        
        # İçe aktarım seçenekleri
        import_scores = request.form.get('import_scores', 'false').lower() == 'true'
        import_notes = request.form.get('import_notes', 'false').lower() == 'true'
        import_dates = request.form.get('import_dates', 'false').lower() == 'true'
        
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []
        new_records_created = 0
        updated_records_count = 0
        
        # Jikan API rate limiting: 1 istek/saniye
        delay_between_requests = 1.2
        
        def fetch_from_jikan(mal_id, record_type):
            """Jikan API'den anime/manga detaylarını çeker."""
            try:
                # Record type'a göre endpoint seç
                if record_type.lower() == 'manga':
                    url = f"https://api.jikan.moe/v4/manga/{mal_id}"
                else:
                    url = f"https://api.jikan.moe/v4/anime/{mal_id}"
                
                response = requests.get(url)
                response.raise_for_status()
                data = response.json().get('data')
                
                if not data:
                    return None
                
                # Parse date string helper
                def parse_date_string(date_string):
                    if not date_string:
                        return None
                    try:
                        if 'T' in date_string:
                            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                        else:
                            return datetime.strptime(date_string, '%Y-%m-%d')
                    except ValueError:
                        return None
                
                # Yeni MasterRecord oluştur
                new_record = MasterRecord(
                    mal_id=mal_id,
                    original_title=data.get('title', ''),
                    english_title=data.get('title_english', ''),
                    record_type='Anime' if record_type.lower() == 'anime' else 'Manga',
                    mal_type=data.get('type', ''),
                    image_url=data.get('images', {}).get('jpg', {}).get('image_url', ''),
                    synopsis=data.get('synopsis', ''),
                    tags=", ".join([g.get('name', '') for g in data.get('genres', []) if g.get('name')]),
                    themes=", ".join([t.get('name', '') for t in data.get('themes', []) if t.get('name')]),
                    source=data.get('source', ''),
                    studios=", ".join([s.get('name', '') for s in data.get('studios', []) if s.get('name')]) if record_type.lower() == 'anime' else '',
                    release_year=data.get('year'),
                    total_episodes=data.get('episodes') if record_type.lower() == 'anime' else data.get('chapters'),
                    score=data.get('score'),
                    popularity=data.get('popularity'),
                    scored_by=data.get('scored_by'),
                    status=data.get('status', ''),
                    aired_from=parse_date_string(data.get('aired', {}).get('from') if record_type.lower() == 'anime' else data.get('published', {}).get('from')),
                    aired_to=parse_date_string(data.get('aired', {}).get('to') if record_type.lower() == 'anime' else data.get('published', {}).get('to')),
                    duration=data.get('duration', '') if record_type.lower() == 'anime' else '',
                    demographics=", ".join([d.get('name', '') for d in data.get('demographics', []) if d.get('name')]),
                    rating=data.get('rating', ''),
                    members=data.get('members'),
                    favorites=data.get('favorites'),
                    relations=str(data.get('relations', [])),
                    licensors=", ".join([l.get('name', '') for l in data.get('licensors', []) if l.get('name')]),
                    producers=", ".join([p.get('name', '') for p in (data.get('producers', []) if record_type.lower() == 'anime' else data.get('authors', [])) if p.get('name')])
                )
                
                return new_record
                
            except Exception as e:
                print(f"Jikan API hatası (MAL ID {mal_id}): {e}")
                return None
        
        for anime in anime_list:
            try:
                # MAL ID'yi al
                mal_id = anime.find('series_animedb_id', namespace)
                if mal_id is None or mal_id.text is None:
                    continue
                
                mal_id = int(mal_id.text)
                
                # MasterRecord'u bul veya oluştur
                master_record = MasterRecord.query.filter_by(mal_id=mal_id).first()
                
                # Check if we need to fetch data (either new record or existing record with missing data)
                needs_data_fetch = False
                if not master_record:
                    needs_data_fetch = True
                elif not master_record.image_url or not master_record.synopsis or not master_record.source:
                    # Existing record but missing key data
                    needs_data_fetch = True
                    print(f"Mevcut kayıt için eksik veri tespit edildi: MAL ID {mal_id}")
                
                if needs_data_fetch:
                    # Jikan API'den detaylı bilgileri çek
                    record_type = anime.find('series_type', namespace)
                    record_type_text = record_type.text if record_type is not None else 'anime'
                    
                    print(f"Jikan API'den veri çekiliyor: MAL ID {mal_id} ({record_type_text})")
                    fetched_record = fetch_from_jikan(mal_id, record_type_text)
                    
                    if fetched_record:
                        if not master_record:
                            # New record
                            master_record = fetched_record
                            db.session.add(master_record)
                            new_records_created += 1
                            print(f"--> Yeni kayıt oluşturuldu: {master_record.original_title}")
                        else:
                            # Update existing record with fetched data
                            master_record.image_url = fetched_record.image_url
                            master_record.synopsis = fetched_record.synopsis
                            master_record.source = fetched_record.source
                            master_record.studios = fetched_record.studios
                            master_record.demographics = fetched_record.demographics
                            master_record.tags = fetched_record.tags
                            master_record.themes = fetched_record.themes
                            master_record.english_title = fetched_record.english_title
                            master_record.mal_type = fetched_record.mal_type
                            master_record.release_year = fetched_record.release_year
                            master_record.total_episodes = fetched_record.total_episodes
                            master_record.score = fetched_record.score
                            master_record.popularity = fetched_record.popularity
                            master_record.scored_by = fetched_record.scored_by
                            master_record.status = fetched_record.status
                            master_record.aired_from = fetched_record.aired_from
                            master_record.aired_to = fetched_record.aired_to
                            master_record.duration = fetched_record.duration
                            master_record.rating = fetched_record.rating
                            master_record.members = fetched_record.members
                            master_record.favorites = fetched_record.favorites
                            master_record.relations = fetched_record.relations
                            master_record.licensors = fetched_record.licensors
                            master_record.producers = fetched_record.producers
                            print(f"--> Mevcut kayıt güncellendi: {master_record.original_title}")
                            updated_records_count += 1
                        
                        db.session.flush()  # ID'yi almak için flush
                        
                        # Rate limiting
                        time.sleep(delay_between_requests)
                    else:
                        # Jikan API'den veri çekilemezse basit kayıt oluştur
                        if not master_record:
                            title = anime.find('series_title', namespace)
                            title_text = title.text if title is not None else f"Unknown {mal_id}"
                            
                            master_record = MasterRecord(
                                mal_id=mal_id,
                                original_title=title_text,
                                record_type='Anime' if record_type_text.lower() == 'anime' else 'Manga',
                                mal_type=record_type_text,
                                total_episodes=int(anime.find('series_episodes', namespace).text) if anime.find('series_episodes', namespace) is not None and anime.find('series_episodes', namespace).text.isdigit() else None
                            )
                            db.session.add(master_record)
                            db.session.flush()
                            print(f"--> Basit kayıt oluşturuldu: {title_text}")
                
                # Kullanıcının listesinde var mı kontrol et
                existing_item = UserList.query.filter_by(
                    user_id=current_user.id, 
                    master_record_id=master_record.id
                ).first()
                
                if existing_item:
                    # Mevcut öğeyi güncelle
                    if import_scores:
                        score = anime.find('my_score', namespace)
                        if score is not None and score.text and score.text.isdigit():
                            existing_item.user_score = int(score.text)
                    
                    if import_notes:
                        comments = anime.find('my_comments', namespace)
                        if comments is not None and comments.text:
                            existing_item.notes = comments.text
                    
                    if import_dates:
                        # İzleme durumunu güncelle
                        status = anime.find('my_status', namespace)
                        if status is not None and status.text:
                            mal_status = status.text.lower()
                            if mal_status == 'completed':
                                existing_item.status = 'Tamamlandı'
                                existing_item.current_chapter = master_record.total_episodes or 0
                            elif mal_status == 'watching':
                                existing_item.status = 'İzleniyor'
                            elif mal_status == 'plan to watch':
                                existing_item.status = 'Planlandı'
                            elif mal_status == 'on-hold':
                                existing_item.status = 'Bırakıldı'
                            elif mal_status == 'dropped':
                                existing_item.status = 'Bırakıldı'
                        
                        # İzlenen bölüm sayısını güncelle
                        watched_eps = anime.find('my_watched_episodes', namespace)
                        if watched_eps is not None and watched_eps.text and watched_eps.text.isdigit():
                            existing_item.current_chapter = int(watched_eps.text)
                    
                    updated_count += 1
                else:
                    # Yeni öğe ekle
                    new_item = UserList(
                        user_id=current_user.id,
                        master_record_id=master_record.id,
                        status='Planlandı',
                        current_chapter=0,
                        user_score=0,
                        notes=''
                    )
                    
                    # Durum ve bölüm bilgilerini ayarla
                    status = anime.find('my_status', namespace)
                    if status is not None and status.text:
                        mal_status = status.text.lower()
                        if mal_status == 'completed':
                            new_item.status = 'Tamamlandı'
                            new_item.current_chapter = master_record.total_episodes or 0
                        elif mal_status == 'watching':
                            new_item.status = 'İzleniyor'
                        elif mal_status == 'plan to watch':
                            new_item.status = 'Planlandı'
                        elif mal_status == 'on-hold':
                            new_item.status = 'Bırakıldı'
                        elif mal_status == 'dropped':
                            new_item.status = 'Bırakıldı'
                    
                    # İzlenen bölüm sayısını ayarla
                    watched_eps = anime.find('my_watched_episodes', namespace)
                    if watched_eps is not None and watched_eps.text and watched_eps.text.isdigit():
                        new_item.current_chapter = int(watched_eps.text)
                    
                    # Puan ve notları ayarla
                    if import_scores:
                        score = anime.find('my_score', namespace)
                        if score is not None and score.text and score.text.isdigit():
                            new_item.user_score = int(score.text)
                        else:
                            new_item.user_score = 0
                    else:
                        new_item.user_score = 0
                    
                    if import_notes:
                        comments = anime.find('my_comments', namespace)
                        if comments is not None and comments.text:
                            new_item.notes = comments.text
                        else:
                            new_item.notes = ''
                    else:
                        new_item.notes = ''
                    
                    db.session.add(new_item)
                    imported_count += 1
                
            except Exception as e:
                errors.append(f"Anime {mal_id}: {str(e)}")
                skipped_count += 1
                continue
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        message = _('İçe aktarım tamamlandı! %(imported)d yeni öğe eklendi, %(updated)d öğe güncellendi, %(skipped)d öğe atlandı.', 
                   imported=imported_count, updated=updated_count, skipped=skipped_count)
        
        if new_records_created > 0:
            message += f" {new_records_created} yeni anime/manga veritabanına eklendi."
        
        if updated_records_count > 0:
            message += f" {updated_records_count} mevcut anime/manga kaydı güncellendi."
        
        if errors:
            message += f" {len(errors)} hata oluştu."
        
        return jsonify({
            'success': True, 
            'message': message,
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'new_records': new_records_created,
            'updated_records': updated_records_count,
            'errors': errors
        })
        
    except ET.ParseError:
        return jsonify({'success': False, 'message': _('XML dosyası parse edilemedi.')}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'{_("İçe aktarım sırasında hata:")} {str(e)}'}), 500

@main_bp.route('/language/<lang>')
def set_language(lang=None):
    """Dil değiştirme endpointi."""
    from flask import session
    if lang in ['tr', 'en']:
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))