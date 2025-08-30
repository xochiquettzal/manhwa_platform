# main.py (Refactored with Service Layer)
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_babel import _
from flask_login import login_required, current_user
from models import db
from services import SearchService, UserListService, TopRecordsService, MALImportService
from services.mal_import_service import ImportOptions
from services.search_service import SearchParams
import logging

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# Initialize services
search_service = SearchService(db.session)
user_list_service = UserListService(db.session)
top_records_service = TopRecordsService(db.session)

@main_bp.route('/')
def index():
    return redirect(url_for('main.search_page'))

@main_bp.route('/my-list')
@login_required
def my_list():
    """Kullanıcının ana paneli - My List sayfası."""
    try:
        user_list, filters = user_list_service.get_user_list(current_user.id)
        
        return render_template(
            'dashboard.html', 
            title=_('Listem'), 
            user_list=user_list,
            tags=filters.tags,
            themes=filters.themes,
            demographics=filters.demographics,
            years=filters.years,
            studios=filters.studios
        )
    except Exception as e:
        logger.error(f"Failed to load user list: {e}")
        flash(_('Liste yüklenirken hata oluştu.'), 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/search')
def search_page():
    """Gelişmiş arama sayfasını render eder."""
    try:
        filters = search_service.get_search_filters()
        
        return render_template(
            'search.html', 
            title=_('Arama'), 
            studios=filters.studios, 
            tags=filters.tags, 
            themes=filters.themes, 
            demographics=filters.demographics, 
            years=filters.years
        )
    except Exception as e:
        logger.error(f"Failed to load search page: {e}")
        flash(_('Arama sayfası yüklenirken hata oluştu.'), 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/top')
def top_records():
    """Weighted Score'a göre sıralanmış Top listesini gösterir."""
    try:
        top_list = top_records_service.get_top_records(50)
        
        return render_template('top_records.html', title=_('En İyiler'), top_list=top_list)
    except Exception as e:
        logger.error(f"Failed to load top records: {e}")
        flash(_('Top liste yüklenirken hata oluştu.'), 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/profile')
@login_required
def profile():
    """Kullanıcı profili ve istatistikleri sayfasını render eder."""
    try:
        # Get user statistics
        stats = user_list_service.get_user_statistics(current_user.id)
        
        # Get chart data
        chart_labels_raw, chart_data = user_list_service.get_chart_data(current_user.id)
        
        # Translate chart labels
        translated_chart_labels = [_(label) for label in chart_labels_raw]
        
        return render_template('profile.html', 
                               title=_('Profilim'), 
                               stats=stats, 
                               chart_labels=translated_chart_labels,
                               chart_data=chart_data)
    except Exception as e:
        logger.error(f"Failed to load profile: {e}")
        flash(_('Profil yüklenirken hata oluştu.'), 'danger')
        return redirect(url_for('main.index'))

# --- API Endpoints ---
@main_bp.route('/api/advanced-search')
def advanced_search():
    """Gelişmiş arama ve sonsuz kaydırma için API."""
    try:
        # Parse search parameters
        search_params = SearchParams(
            query=request.args.get('q', '', type=str),
            tags=request.args.get('tags', '', type=str),
            themes=request.args.get('themes', '', type=str),
            demographics=request.args.get('demographics', '', type=str),
            year=request.args.get('year', '', type=str),
            studio=request.args.get('studio', '', type=str),
            sort_by=request.args.get('sort_by', 'popularity', type=str),
            page=request.args.get('page', 1, type=int),
            per_page=20
        )
        
        # Perform search
        search_result = search_service.advanced_search(search_params)
        
        return jsonify({
            'results': search_result.results,
            'has_next': search_result.has_next
        })
        
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500

@main_bp.route('/list/update/<int:user_list_id>', methods=['POST'])
@login_required
def update_list_item(user_list_id):
    """Update user list item"""
    try:
        data = request.get_json()
        
        success, message = user_list_service.update_list_item(
            current_user.id, 
            user_list_id, 
            data
        )
        
        if success:
            if not data.get('silent'):
                flash(_(message), "success")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': _(message)}), 400
            
    except Exception as e:
        logger.error(f"Failed to update list item: {e}")
        return jsonify({'success': False, 'message': _('Güncelleme sırasında hata oluştu.')}), 500

@main_bp.route('/list/add/<int:record_id>', methods=['POST'])
@login_required
def add_to_list(record_id):
    """Add item to user's list"""
    try:
        success, message = user_list_service.add_to_list(current_user.id, record_id)
        
        if success:
            return jsonify({'success': True, 'message': _(message)})
        else:
            return jsonify({'success': False, 'message': _(message)}), 409
            
    except Exception as e:
        logger.error(f"Failed to add item to list: {e}")
        return jsonify({'success': False, 'message': _('Listeye ekleme sırasında hata oluştu.')}), 500

@main_bp.route('/list/delete/<int:user_list_id>', methods=['POST'])
@login_required
def delete_list_item(user_list_id):
    """Delete item from user's list"""
    try:
        success, message = user_list_service.delete_list_item(current_user.id, user_list_id)
        
        if success:
            return jsonify({'success': True, 'message': _(message)})
        else:
            return jsonify({'success': False, 'message': _(message)}), 400
            
    except Exception as e:
        logger.error(f"Failed to delete list item: {e}")
        return jsonify({'success': False, 'message': _('Silme sırasında hata oluştu.')}), 500

@main_bp.route('/api/record/<int:record_id>')
def get_record_details(record_id):
    """Search modalı için kayıt detaylarını döndürür."""
    try:
        record_details = search_service.get_record_details(record_id)
        
        if record_details:
            return jsonify(record_details)
        else:
            return jsonify({'error': 'Record not found'}), 404
            
    except Exception as e:
        logger.error(f"Failed to get record details: {e}")
        return jsonify({'error': 'Failed to get record details'}), 500

@main_bp.route('/import/mal', methods=['POST'])
@login_required
def import_mal_list():
    """MyAnimeList XML export dosyasını içe aktarır."""
    try:
        # Check if file was uploaded
        if 'mal_file' not in request.files:
            return jsonify({'success': False, 'message': _('Dosya yüklenmedi.')}), 400
        
        file = request.files['mal_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': _('Dosya seçilmedi.')}), 400
        
        if not file.filename.endswith('.xml'):
            return jsonify({'success': False, 'message': _('Sadece XML dosyaları desteklenir.')}), 400
        
        # Parse import options
        import_options = ImportOptions(
            import_scores=request.form.get('import_scores', 'false').lower() == 'true',
            import_notes=request.form.get('import_notes', 'false').lower() == 'true',
            import_dates=request.form.get('import_dates', 'false').lower() == 'true'
        )
        
        # Perform import using service
        mal_import_service = MALImportService(db.session)
        import_result = mal_import_service.import_user_list(file, current_user.id, import_options)
        
        if import_result.success:
            # Clear search cache since new records might have been added
            search_service.clear_cache()
            
            return jsonify({
                'success': True,
                'message': _(import_result.message),
                'imported': import_result.imported_count,
                'updated': import_result.updated_count,
                'skipped': import_result.skipped_count,
                'new_records': import_result.new_records_created,
                'updated_records': import_result.updated_records_count,
                'errors': import_result.errors
            })
        else:
            return jsonify({'success': False, 'message': _(import_result.message)}), 400
            
    except Exception as e:
        logger.error(f"MAL import failed: {e}")
        return jsonify({'success': False, 'message': f'{_("İçe aktarım sırasında hata:")} {str(e)}'}), 500

@main_bp.route('/language/<lang>')
def set_language(lang=None):
    """Dil değiştirme endpointi."""
    if lang in ['tr', 'en']:
        from flask import session
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))