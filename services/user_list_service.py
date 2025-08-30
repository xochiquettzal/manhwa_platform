# services/user_list_service.py
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from models import UserList, MasterRecord
from flask_login import current_user
from dataclasses import dataclass
import logging
from extensions import db

logger = logging.getLogger(__name__)

@dataclass
class UserListStats:
    total: int
    watching: int
    reading: int
    completed: int
    planned: int
    dropped: int
    avg_score: str
    total_chapters: int

@dataclass
class UserListFilters:
    tags: List[str]
    themes: List[str]
    demographics: List[str]
    years: List[int]
    studios: List[str]

class UserListService:
    """Handles user list operations and statistics"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def get_user_list(self, user_id: int) -> Tuple[List[Dict], UserListFilters]:
        """Get user's list with optimized query and filters"""
        try:
            # Single optimized query to get user list with master records
            user_list_items = self.db_session.query(
                UserList, MasterRecord
            ).join(
                MasterRecord
            ).filter(
                UserList.user_id == user_id
            ).all()
            
            # Extract filter data from results
            filters = self._extract_filters_from_results(user_list_items)
            
            # Format results
            formatted_list = self._format_user_list(user_list_items)
            
            return formatted_list, filters
            
        except Exception as e:
            logger.error(f"Failed to get user list for user {user_id}: {e}")
            return [], UserListFilters([], [], [], [], [])
    
    def get_user_statistics(self, user_id: int) -> UserListStats:
        """Get user statistics with optimized queries"""
        try:
            # Get status counts in single query
            status_counts = self.db_session.query(
                UserList.status,
                func.count(UserList.id)
            ).filter_by(
                user_id=user_id
            ).group_by(
                UserList.status
            ).all()
            
            # Convert to dictionary for easy access
            status_counts_dict = {status: count for status, count in status_counts}
            
            # Get average score (excluding 0 scores)
            avg_score = self.db_session.query(
                func.avg(UserList.user_score)
            ).filter(
                UserList.user_id == user_id,
                UserList.user_score > 0
            ).scalar()
            
            # Get total chapters
            total_chapters = self.db_session.query(
                func.sum(UserList.current_chapter)
            ).filter_by(
                user_id=user_id
            ).scalar()
            
            return UserListStats(
                total=sum(status_counts_dict.values()),
                watching=status_counts_dict.get('İzleniyor', 0),
                reading=status_counts_dict.get('Okunuyor', 0),
                completed=status_counts_dict.get('Tamamlandı', 0),
                planned=status_counts_dict.get('Planlandı', 0),
                dropped=status_counts_dict.get('Bırakıldı', 0),
                avg_score=f"{avg_score:.2f}" if avg_score else "N/A",
                total_chapters=total_chapters or 0
            )
            
        except Exception as e:
            logger.error(f"Failed to get user statistics for user {user_id}: {e}")
            return UserListStats(0, 0, 0, 0, 0, 0, "N/A", 0)
    
    def get_chart_data(self, user_id: int) -> Tuple[List[str], List[int]]:
        """Get chart data for user statistics"""
        try:
            # Get status counts for chart
            status_counts = self.db_session.query(
                UserList.status,
                func.count(UserList.id)
            ).filter_by(
                user_id=user_id
            ).group_by(
                UserList.status
            ).all()
            
            # Extract labels and data
            labels = [status for status, _ in status_counts]
            data = [count for _, count in status_counts]
            
            return labels, data
            
        except Exception as e:
            logger.error(f"Failed to get chart data for user {user_id}: {e}")
            return [], []
    
    def add_to_list(self, user_id: int, record_id: int) -> Tuple[bool, str]:
        """Add item to user's list"""
        try:
            # Check if already exists
            existing_entry = UserList.query.filter_by(
                user_id=user_id,
                master_record_id=record_id
            ).first()
            
            if existing_entry:
                return False, "This record is already in your list."
            
            # Verify master record exists
            master_record = db.session.get(MasterRecord, record_id)
            if not master_record:
                return False, "Record not found."
            
            # Create new list item
            new_list_item = UserList(
                user_id=user_id,
                master_record_id=record_id,
                status='Planlandı'
            )
            
            self.db_session.add(new_list_item)
            self.db_session.commit()
            
            return True, f"'{master_record.original_title}' successfully added to your list!"
            
        except Exception as e:
            logger.error(f"Failed to add item to list: {e}")
            self.db_session.rollback()
            return False, "Failed to add item to list."
    
    def update_list_item(self, user_id: int, user_list_id: int, update_data: Dict) -> Tuple[bool, str]:
        """Update user list item"""
        try:
            # Get and validate item
            item = UserList.query.get_or_404(user_list_id)
            if item.user_id != user_id:
                return False, "Unauthorized operation."
            
            # Update fields
            if 'status' in update_data:
                item.status = update_data['status']
            
            if 'current_chapter' in update_data:
                requested_chapter = update_data['current_chapter']
                try:
                    requested_chapter = int(requested_chapter)
                except (ValueError, TypeError):
                    requested_chapter = item.current_chapter
                
                # Validate chapter number
                total_eps = item.record.total_episodes or 0
                if total_eps and requested_chapter > total_eps:
                    requested_chapter = total_eps
                if requested_chapter < 0:
                    requested_chapter = 0
                
                item.current_chapter = requested_chapter
            
            if 'user_score' in update_data:
                score = update_data['user_score']
                try:
                    score = int(score)
                    if 0 <= score <= 10:
                        item.user_score = score
                except (ValueError, TypeError):
                    pass  # Keep existing score
            
            if 'notes' in update_data:
                item.notes = update_data['notes']
            
            self.db_session.commit()
            
            return True, "Record successfully updated!"
            
        except Exception as e:
            logger.error(f"Failed to update list item: {e}")
            self.db_session.rollback()
            return False, "Failed to update record."
    
    def delete_list_item(self, user_id: int, user_list_id: int) -> Tuple[bool, str]:
        """Delete item from user's list"""
        try:
            # Get and validate item
            item = UserList.query.get_or_404(user_list_id)
            if item.user_id != user_id:
                return False, "Unauthorized operation."
            
            self.db_session.delete(item)
            self.db_session.commit()
            
            return True, "Record successfully removed from your list."
            
        except Exception as e:
            logger.error(f"Failed to delete list item: {e}")
            self.db_session.rollback()
            return False, "Failed to remove record."
    
    def _extract_filters_from_results(self, user_list_items: List[Tuple[UserList, MasterRecord]]) -> UserListFilters:
        """Extract filter data from user list results"""
        all_tags, all_themes, all_demographics, years, studios = set(), set(), set(), set(), set()
        
        for _, record in user_list_items:
            if record and record.tags:
                for tag in record.tags.split(','):
                    all_tags.add(tag.strip())
            
            if record and record.themes:
                for theme in record.themes.split(','):
                    all_themes.add(theme.strip())
            
            if record and record.demographics:
                for demo in record.demographics.split(','):
                    all_demographics.add(demo.strip())
            
            if record and record.release_year:
                years.add(record.release_year)
            
            if record and record.studios:
                studios.add(record.studios)
        
        return UserListFilters(
            tags=sorted(list(all_tags)),
            themes=sorted(list(all_themes)),
            demographics=sorted(list(all_demographics)),
            years=sorted(list(years), reverse=True),
            studios=sorted(list(studios))
        )
    
    def _format_user_list(self, user_list_items: List[Tuple[UserList, MasterRecord]]) -> List[Dict]:
        """Format user list items for template rendering"""
        formatted_list = []
        
        for user_list_obj, record_obj in user_list_items:
            try:
                formatted_item = {
                    'list_item': user_list_obj,
                    'record': record_obj
                }
                formatted_list.append(formatted_item)
            except Exception as e:
                logger.error(f"Failed to format list item: {e}")
                continue
        
        return formatted_list
