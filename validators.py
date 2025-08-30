# validators.py
import re
from typing import Any, Dict, List, Optional, Union
from exceptions import ValidationError

class Validator:
    """Base validator class"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """Validate that a required field is not empty"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required")
    
    @staticmethod
    def validate_string_length(value: str, field_name: str, min_length: int = 0, max_length: int = None) -> None:
        """Validate string length constraints"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters long")
        
        if max_length and len(value) > max_length:
            raise ValidationError(f"{field_name} must be no more than {max_length} characters long")
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format"""
        if not email:
            return
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
    
    @staticmethod
    def validate_username(username: str) -> None:
        """Validate username format"""
        if not username:
            return
        
        # Username should be 3-20 characters, alphanumeric and underscores only
        username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
        if not re.match(username_pattern, username):
            raise ValidationError("Username must be 3-20 characters long and contain only letters, numbers, and underscores")
    
    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password strength"""
        if not password:
            return
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValidationError("Password must be no more than 128 characters long")
    
    @staticmethod
    def validate_integer_range(value: Any, field_name: str, min_value: int = None, max_value: int = None) -> None:
        """Validate integer value is within range"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} must be no more than {max_value}")
    
    @staticmethod
    def validate_float_range(value: Any, field_name: str, min_value: float = None, max_value: float = None) -> None:
        """Validate float value is within range"""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number")
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name} must be no more than {max_value}")
    
    @staticmethod
    def validate_choice(value: Any, field_name: str, valid_choices: List[Any]) -> None:
        """Validate that value is one of the valid choices"""
        if value not in valid_choices:
            raise ValidationError(f"{field_name} must be one of: {', '.join(map(str, valid_choices))}")
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> None:
        """Validate file extension"""
        if not filename:
            raise ValidationError("Filename is required")
        
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if file_extension not in allowed_extensions:
            raise ValidationError(f"File extension must be one of: {', '.join(allowed_extensions)}")
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_bytes: int) -> None:
        """Validate file size"""
        if file_size > max_size_bytes:
            max_size_mb = max_size_bytes / (1024 * 1024)
            raise ValidationError(f"File size must be no more than {max_size_mb:.1f} MB")

class SearchParamsValidator(Validator):
    """Validator for search parameters"""
    
    @staticmethod
    def validate_search_params(params: Dict[str, Any]) -> None:
        """Validate search parameters"""
        # Validate page number
        if 'page' in params:
            Validator.validate_integer_range(params['page'], 'page', 1, 100)
        
        # Validate per_page
        if 'per_page' in params:
            Validator.validate_integer_range(params['per_page'], 'per_page', 1, 100)
        
        # Validate sort_by
        valid_sort_options = ['popularity', 'score', 'title', 'year']
        if 'sort_by' in params:
            Validator.validate_choice(params['sort_by'], 'sort_by', valid_sort_options)
        
        # Validate year if provided
        if 'year' in params and params['year']:
            try:
                year = int(params['year'])
                if year < 1900 or year > 2100:
                    raise ValidationError("Year must be between 1900 and 2100")
            except ValueError:
                raise ValidationError("Year must be a valid integer")

class UserListValidator(Validator):
    """Validator for user list operations"""
    
    @staticmethod
    def validate_list_item_update(data: Dict[str, Any]) -> None:
        """Validate user list item update data"""
        # Validate status if provided
        if 'status' in data:
            valid_statuses = ['Planlandı', 'İzleniyor', 'Okunuyor', 'Tamamlandı', 'Bırakıldı']
            Validator.validate_choice(data['status'], 'status', valid_statuses)
        
        # Validate current_chapter if provided
        if 'current_chapter' in data:
            Validator.validate_integer_range(data['current_chapter'], 'current_chapter', 0)
        
        # Validate user_score if provided
        if 'user_score' in data:
            Validator.validate_integer_range(data['user_score'], 'user_score', 0, 10)

class ImportValidator(Validator):
    """Validator for import operations"""
    
    @staticmethod
    def validate_import_options(options: Dict[str, Any]) -> None:
        """Validate import options"""
        # All import options should be boolean
        for key, value in options.items():
            if not isinstance(value, bool):
                raise ValidationError(f"Import option {key} must be a boolean")
    
    @staticmethod
    def validate_xml_file(file) -> None:
        """Validate XML file for import"""
        if not file:
            raise ValidationError("No file provided")
        
        if file.filename == '':
            raise ValidationError("No file selected")
        
        Validator.validate_file_extension(file.filename, ['xml'])
        
        # Check file size (16MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        Validator.validate_file_size(file_size, 16 * 1024 * 1024)
