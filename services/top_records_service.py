# services/top_records_service.py
from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import MasterRecord
import logging

logger = logging.getLogger(__name__)

class TopRecordsService:
    """Handles top records calculations and retrieval"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.min_votes = 1000  # Minimum votes for weighted score calculation
        self.default_score = 7.0  # Default score for records with few votes
    
    def get_top_records(self, limit: int = 50) -> List[Tuple[MasterRecord, float]]:
        """Get top records based on weighted score"""
        try:
            # Calculate weighted score using Bayesian average
            weighted_score_formula = self._calculate_weighted_score_formula()
            
            # Query top records
            top_list_query = self.db_session.query(
                MasterRecord, 
                weighted_score_formula
            ).filter(
                MasterRecord.scored_by >= self.min_votes,
                MasterRecord.score.isnot(None)
            ).order_by(
                weighted_score_formula.desc()
            ).limit(limit).all()
            
            # Return as tuples (record, weighted_score) for template compatibility
            top_records = []
            for record, weighted_score in top_list_query:
                top_records.append((record, float(weighted_score)))
            
            return top_records
            
        except Exception as e:
            logger.error(f"Failed to get top records: {e}")
            return []
    
    def _calculate_weighted_score_formula(self):
        """Calculate the weighted score formula using Bayesian average"""
        # Get average score from database
        avg_score = self.db_session.query(
            func.avg(MasterRecord.score)
        ).filter(
            MasterRecord.score.isnot(None)
        ).scalar() or self.default_score
        
        # Bayesian average formula: (v * R + m * C) / (v + m)
        # where v = votes, R = rating, m = minimum votes, C = average rating
        weighted_score = (
            (MasterRecord.scored_by / (MasterRecord.scored_by + self.min_votes)) * MasterRecord.score +
            (self.min_votes / (MasterRecord.scored_by + self.min_votes)) * avg_score
        ).label('weighted_score')
        
        return weighted_score
    
    def get_top_records_by_genre(self, genre: str, limit: int = 25) -> List[Tuple[MasterRecord, float]]:
        """Get top records filtered by specific genre/tag"""
        try:
            weighted_score_formula = self._calculate_weighted_score_formula()
            
            # Query with genre filter
            top_list_query = self.db_session.query(
                MasterRecord, 
                weighted_score_formula
            ).filter(
                MasterRecord.scored_by >= self.min_votes,
                MasterRecord.score.isnot(None),
                MasterRecord.tags.ilike(f"%{genre}%")
            ).order_by(
                weighted_score_formula.desc()
            ).limit(limit).all()
            
            # Return as tuples (record, weighted_score) for template compatibility
            top_records = []
            for record, weighted_score in top_list_query:
                top_records.append((record, float(weighted_score)))
            
            return top_records
            
        except Exception as e:
            logger.error(f"Failed to get top records by genre {genre}: {e}")
            return []
    
    def get_top_records_by_year(self, year: int, limit: int = 25) -> List[Tuple[MasterRecord, float]]:
        """Get top records filtered by specific year"""
        try:
            weighted_score_formula = self._calculate_weighted_score_formula()
            
            # Query with year filter
            top_list_query = self.db_session.query(
                MasterRecord, 
                weighted_score_formula
            ).filter(
                MasterRecord.scored_by >= self.min_votes,
                MasterRecord.score.isnot(None),
                MasterRecord.release_year == year
            ).order_by(
                weighted_score_formula.desc()
            ).limit(limit).all()
            
            # Return as tuples (record, weighted_score) for template compatibility
            top_records = []
            for record, weighted_score in top_list_query:
                top_records.append((record, float(weighted_score)))
            
            return top_records
            
        except Exception as e:
            logger.error(f"Failed to get top records for year {year}: {e}")
            return []
