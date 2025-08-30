# services/search_service.py
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
from sqlalchemy import func, distinct, or_, and_
from sqlalchemy.orm import Session
from models import MasterRecord, UserList
from flask_login import current_user
import logging
from dataclasses import dataclass
from extensions import db

logger = logging.getLogger(__name__)

@dataclass
class SearchFilters:
    studios: List[str]
    tags: List[str]
    themes: List[str]
    demographics: List[str]
    years: List[int]

@dataclass
class SearchParams:
    query: str = ''
    tags: str = ''
    themes: str = ''
    demographics: str = ''
    year: str = ''
    studio: str = ''
    sort_by: str = 'popularity'
    page: int = 1
    per_page: int = 20

@dataclass
class SearchResult:
    results: List[Dict]
    has_next: bool
    total_count: int

class SearchService:
    """Handles search operations with optimized queries and caching"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    @lru_cache(maxsize=1)
    def get_search_filters(self) -> SearchFilters:
        """Get all search filters in a single optimized query with caching"""
        try:
            # Single query to get all filter data
            filter_data = self.db_session.query(
                func.group_concat(distinct(MasterRecord.studios)).label('studios'),
                func.group_concat(distinct(MasterRecord.tags)).label('tags'),
                func.group_concat(distinct(MasterRecord.themes)).label('themes'),
                func.group_concat(distinct(MasterRecord.demographics)).label('demographics'),
                func.group_concat(distinct(MasterRecord.release_year)).label('years')
            ).filter(
                or_(
                    MasterRecord.studios.isnot(None),
                    MasterRecord.tags.isnot(None),
                    MasterRecord.themes.isnot(None),
                    MasterRecord.demographics.isnot(None),
                    MasterRecord.release_year.isnot(None)
                )
            ).first()
            
            return SearchFilters(
                studios=self._parse_comma_separated(filter_data.studios),
                tags=self._parse_comma_separated(filter_data.tags),
                themes=self._parse_comma_separated(filter_data.themes),
                demographics=self._parse_comma_separated(filter_data.demographics),
                years=self._parse_years(filter_data.years)
            )
        except Exception as e:
            logger.error(f"Failed to get search filters: {e}")
            return SearchFilters([], [], [], [], [])
    
    def advanced_search(self, search_params: SearchParams) -> SearchResult:
        """Perform advanced search with optimized query building"""
        try:
            # Build base query
            base_query = self._build_search_query(search_params)
            
            # Apply sorting
            base_query = self._apply_sorting(base_query, search_params.sort_by)
            
            # Get pagination info
            pagination = base_query.paginate(
                page=search_params.page, 
                per_page=search_params.per_page, 
                error_out=False
            )
            
            # Get results
            results = pagination.items
            
            # Get user list record IDs for current user
            user_list_record_ids = self._get_user_list_record_ids()
            
            # Format results
            formatted_results = self._format_search_results(results, user_list_record_ids)
            
            return SearchResult(
                results=formatted_results,
                has_next=pagination.has_next,
                total_count=pagination.total
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SearchResult([], False, 0)
    
    def _build_search_query(self, search_params: SearchParams):
        """Build the base search query with filters"""
        base_query = MasterRecord.query
        
        # Text search
        if search_params.query:
            search_term = f"%{search_params.query}%"
            base_query = base_query.filter(
                or_(
                    MasterRecord.original_title.ilike(search_term),
                    MasterRecord.english_title.ilike(search_term)
                )
            )
        
        # Tags filter
        if search_params.tags:
            tag_list = [f"%{tag.strip()}%" for tag in search_params.tags.split(',')]
            for tag in tag_list:
                base_query = base_query.filter(MasterRecord.tags.ilike(tag))
        
        # Themes filter
        if search_params.themes:
            theme_list = [f"%{t.strip()}%" for t in search_params.themes.split(',')]
            for t in theme_list:
                base_query = base_query.filter(MasterRecord.themes.ilike(t))
        
        # Demographics filter
        if search_params.demographics:
            demo_list = [f"%{d.strip()}%" for d in search_params.demographics.split(',')]
            for d in demo_list:
                base_query = base_query.filter(MasterRecord.demographics.ilike(d))
        
        # Studio filter
        if search_params.studio:
            base_query = base_query.filter(MasterRecord.studios == search_params.studio)
        
        # Year filter
        if search_params.year:
            try:
                year_int = int(search_params.year)
                base_query = base_query.filter(MasterRecord.release_year == year_int)
            except ValueError:
                pass  # Invalid year, ignore filter
        
        return base_query
    
    def _apply_sorting(self, query, sort_by: str):
        """Apply sorting to the query"""
        if sort_by == 'score':
            return query.order_by(MasterRecord.score.desc().nullslast())
        elif sort_by == 'title':
            return query.order_by(MasterRecord.original_title.asc())
        elif sort_by == 'year':
            return query.order_by(MasterRecord.release_year.desc().nullslast())
        else:  # Default: popularity
            return query.order_by(MasterRecord.popularity.asc().nullslast())
    
    def _get_user_list_record_ids(self) -> set:
        """Get current user's list record IDs"""
        if not current_user.is_authenticated:
            return set()
        
        try:
            user_list_ids = self.db_session.query(UserList.master_record_id).filter(
                UserList.user_id == current_user.id
            ).all()
            return {item[0] for item in user_list_ids}
        except Exception as e:
            logger.error(f"Failed to get user list IDs: {e}")
            return set()
    
    def _format_search_results(self, results: List[MasterRecord], user_list_record_ids: set) -> List[Dict]:
        """Format search results for JSON response"""
        formatted_results = []
        
        for record in results:
            try:
                formatted_record = {
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
                }
                formatted_results.append(formatted_record)
            except Exception as e:
                logger.error(f"Failed to format record {record.id}: {e}")
                continue
        
        return formatted_results
    
    def _parse_comma_separated(self, value: str) -> List[str]:
        """Parse comma-separated string into list"""
        if not value:
            return []
        
        try:
            parsed = [tag.strip() for tag in value.split(',') if tag.strip()]
            return sorted(list(set(parsed)))  # Remove duplicates and sort
        except Exception as e:
            logger.error(f"Failed to parse comma-separated value: {e}")
            return []
    
    def _parse_years(self, years_str: str) -> List[int]:
        """Parse years string into sorted list of integers"""
        if not years_str:
            return []
        
        try:
            years = []
            for year_str in years_str.split(','):
                if year_str.strip().isdigit():
                    years.append(int(year_str.strip()))
            return sorted(years, reverse=True)  # Most recent first
        except Exception as e:
            logger.error(f"Failed to parse years: {e}")
            return []
    
    def get_record_details(self, record_id: int) -> Optional[Dict]:
        """Get detailed record information for search modal"""
        try:
            record = db.session.get(MasterRecord, record_id)
            if not record:
                return None
            
            return {
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
            }
        except Exception as e:
            logger.error(f"Failed to get record details for {record_id}: {e}")
            return None
    
    def clear_cache(self):
        """Clear the search filters cache"""
        self.get_search_filters.cache_clear()
