# tests/test_services.py
import pytest
from unittest.mock import Mock, patch
from services.search_service import SearchService, SearchParams
from services.user_list_service import UserListService
from services.mal_import_service import MALImportService, ImportOptions
from exceptions import ValidationError

class TestSearchService:
    """Test cases for SearchService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_session = Mock()
        self.search_service = SearchService(self.mock_session)
    
    def test_get_search_filters_success(self):
        """Test successful retrieval of search filters"""
        # Mock database query result
        mock_result = Mock()
        mock_result.studios = "Studio A,Studio B"
        mock_result.tags = "Action,Comedy"
        mock_result.themes = "Dark,Light"
        mock_result.demographics = "Shounen,Seinen"
        mock_result.years = "2020,2021,2022"
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_result
        
        filters = self.search_service.get_search_filters()
        
        assert filters.studios == ["Studio A", "Studio B"]
        assert filters.tags == ["Action", "Comedy"]
        assert filters.themes == ["Dark", "Light"]
        assert filters.demographics == ["Shounen", "Seinen"]
        assert filters.years == [2022, 2021, 2020]
    
    def test_get_search_filters_empty(self):
        """Test handling of empty filter results"""
        mock_result = Mock()
        mock_result.studios = None
        mock_result.tags = None
        mock_result.themes = None
        mock_result.demographics = None
        mock_result.years = None
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_result
        
        filters = self.search_service.get_search_filters()
        
        assert filters.studios == []
        assert filters.tags == []
        assert filters.themes == []
        assert filters.demographics == []
        assert filters.years == []

class TestUserListService:
    """Test cases for UserListService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_session = Mock()
        self.user_list_service = UserListService(self.mock_session)
    
    def test_get_user_statistics_success(self):
        """Test successful retrieval of user statistics"""
        # Mock status counts query
        mock_status_counts = [("İzleniyor", 5), ("Tamamlandı", 3), ("Planlandı", 2)]
        self.mock_session.query.return_value.filter_by.return_value.group_by.return_value.all.return_value = mock_status_counts
        
        # Mock average score query
        self.mock_session.query.return_value.filter.return_value.scalar.return_value = 8.5
        
        # Mock total chapters query
        self.mock_session.query.return_value.filter_by.return_value.scalar.return_value = 150
        
        stats = self.user_list_service.get_user_statistics(1)
        
        assert stats.total == 10
        assert stats.watching == 5
        assert stats.completed == 3
        assert stats.planned == 2
        assert stats.avg_score == "8.50"
        assert stats.total_chapters == 150

class TestMALImportService:
    """Test cases for MALImportService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_session = Mock()
        self.import_service = MALImportService(self.mock_session)
    
    def test_import_options_validation(self):
        """Test import options validation"""
        options = ImportOptions(
            import_scores=True,
            import_notes=False,
            import_dates=True
        )
        
        assert options.import_scores is True
        assert options.import_notes is False
        assert options.import_dates is True
    
    @patch('services.mal_import_service.JikanAPIClient')
    def test_jikan_api_client_initialization(self, mock_jikan):
        """Test Jikan API client initialization"""
        mock_client = Mock()
        mock_jikan.return_value = mock_client
        
        # The service should create a Jikan client
        assert self.import_service.jikan_client is not None

class TestValidation:
    """Test cases for validation functions"""
    
    def test_search_params_validation(self):
        """Test search parameters validation"""
        from validators import SearchParamsValidator
        
        # Valid parameters
        valid_params = {
            'page': 1,
            'per_page': 20,
            'sort_by': 'popularity',
            'year': '2020'
        }
        
        # Should not raise any exceptions
        SearchParamsValidator.validate_search_params(valid_params)
    
    def test_search_params_validation_invalid_page(self):
        """Test validation with invalid page number"""
        from validators import SearchParamsValidator, ValidationError
        
        invalid_params = {'page': 0}  # Page must be >= 1
        
        with pytest.raises(ValidationError, match="page must be at least 1"):
            SearchParamsValidator.validate_search_params(invalid_params)
    
    def test_search_params_validation_invalid_sort(self):
        """Test validation with invalid sort option"""
        from validators import SearchParamsValidator, ValidationError
        
        invalid_params = {'sort_by': 'invalid_sort'}
        
        with pytest.raises(ValidationError, match="sort_by must be one of"):
            SearchParamsValidator.validate_search_params(invalid_params)

class TestExceptions:
    """Test cases for custom exceptions"""
    
    def test_manhwa_platform_error_inheritance(self):
        """Test exception inheritance hierarchy"""
        from exceptions import (
            ManhwaPlatformError, ValidationError, 
            AuthenticationError, DatabaseError
        )
        
        # Test inheritance
        assert issubclass(ValidationError, ManhwaPlatformError)
        assert issubclass(AuthenticationError, ManhwaPlatformError)
        assert issubclass(DatabaseError, ManhwaPlatformError)
    
    def test_exception_message(self):
        """Test exception message formatting"""
        from exceptions import ValidationError
        
        error = ValidationError("Test validation error")
        assert str(error) == "Test validation error"

if __name__ == "__main__":
    pytest.main([__file__])
