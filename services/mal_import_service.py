# services/mal_import_service.py
import xml.etree.ElementTree as ET
import requests
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from models import MasterRecord, UserList
import logging

logger = logging.getLogger(__name__)

@dataclass
class ImportResult:
    success: bool
    message: str
    imported_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    new_records_created: int = 0
    updated_records_count: int = 0
    errors: List[str] = None

@dataclass
class ImportOptions:
    import_scores: bool = False
    import_notes: bool = False
    import_dates: bool = False

class JikanAPIClient:
    """Handles Jikan API requests with rate limiting"""
    
    def __init__(self, delay_between_requests: float = 1.0):  # Optimized for 60 requests/minute
        self.delay = delay_between_requests
        self.base_url = "https://api.jikan.moe/v4"
    
    def fetch_anime(self, mal_id: int) -> Optional[Dict[str, Any]]:
        """Fetch anime data from Jikan API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/anime/{mal_id}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json().get('data')
                time.sleep(self.delay)  # Rate limiting
                return data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    wait_time = (attempt + 1) * 5  # Progressive backoff
                    logger.warning(f"Rate limited for anime {mal_id}, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error for anime {mal_id}: {e}")
                    return None
            except Exception as e:
                logger.error(f"Failed to fetch anime {mal_id}: {e}")
                return None
        
        logger.error(f"Failed to fetch anime {mal_id} after {max_retries} attempts")
        return None
    
    def fetch_manga(self, mal_id: int) -> Optional[Dict[str, Any]]:
        """Fetch manga data from Jikan API with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/manga/{mal_id}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json().get('data')
                time.sleep(self.delay)  # Rate limiting
                return data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    wait_time = (attempt + 1) * 5  # Progressive backoff
                    logger.warning(f"Rate limited for manga {mal_id}, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error for manga {mal_id}: {e}")
                    return None
            except Exception as e:
                logger.error(f"Failed to fetch manga {mal_id}: {e}")
                return None
        
        logger.error(f"Failed to fetch manga {mal_id} after {max_retries} attempts")
        return None

class MALImportService:
    """Handles MyAnimeList XML import operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.jikan_client = JikanAPIClient()
        self.namespace = {'mal': 'http://myanimelist.net/xsd/1.0'}
    
    def import_user_list(self, xml_file, user_id: int, import_options: ImportOptions) -> ImportResult:
        """Main import method for MAL XML files"""
        try:
            # Validate input
            if not xml_file or xml_file.filename == '':
                return ImportResult(False, "No file provided")
            
            if not xml_file.filename.endswith('.xml'):
                return ImportResult(False, "Only XML files are supported")
            
            # Parse XML
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
            except ET.ParseError as e:
                return ImportResult(False, f"Invalid XML file: {str(e)}")
            
            # Validate MAL format
            user_info = root.find('myinfo', self.namespace)
            if user_info is None:
                return ImportResult(False, "Invalid MyAnimeList export file")
            
            anime_list = root.findall('anime', self.namespace)
            if not anime_list:
                return ImportResult(False, "No anime list found in file")
            
            # Process import
            result = self._process_anime_list(anime_list, user_id, import_options)
            return result
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            self.db_session.rollback()
            return ImportResult(False, f"Import failed: {str(e)}")
    
    def _process_anime_list(self, anime_list, user_id: int, import_options: ImportOptions) -> ImportResult:
        """Process the anime list from XML with optimized bulk processing"""
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        new_records_created = 0
        updated_records_count = 0
        errors = []
        
        total_anime = len(anime_list)
        logger.info(f"Processing {total_anime} anime with optimized bulk processing")
        
        # STEP 1: Extract all MAL IDs from XML
        logger.info("Step 1: Extracting MAL IDs from XML...")
        anime_data = []
        for anime in anime_list:
            mal_id = self._extract_mal_id(anime)
            if mal_id:
                anime_data.append((anime, mal_id))
            else:
                skipped_count += 1
        
        if not anime_data:
            return ImportResult(False, "No valid anime found in XML")
        
        valid_mal_ids = [mal_id for _, mal_id in anime_data]
        logger.info(f"Found {len(valid_mal_ids)} valid MAL IDs, skipped {skipped_count} invalid")
        
        # STEP 2: Single query to check existing records - MAJOR PERFORMANCE BOOST!
        logger.info("Step 2: Checking existing records in database (single query)...")
        existing_records = MasterRecord.query.filter(
            MasterRecord.mal_id.in_(valid_mal_ids)
        ).all()
        
        existing_mal_ids = {record.mal_id: record for record in existing_records}
        missing_mal_ids = set(valid_mal_ids) - set(existing_mal_ids.keys())
        
        logger.info(f"Found {len(existing_records)} existing records")
        logger.info(f"Need to fetch {len(missing_mal_ids)} missing records from Jikan API")
        
        # STEP 3: Fetch missing records from Jikan API (sequential processing)
        if missing_mal_ids:
            logger.info("Step 3: Fetching missing records from Jikan API...")
            missing_list = list(missing_mal_ids)
            total_missing = len(missing_list)
            
            for index, mal_id in enumerate(missing_list, 1):
                logger.info(f"Processing {index}/{total_missing}: Anime {mal_id}")
                
                try:
                    # Find the anime element for this MAL ID
                    anime_element = None
                    for anime, aid in anime_data:
                        if aid == mal_id:
                            anime_element = anime
                            break
                    
                    if not anime_element:
                        continue
                    
                    # Fetch from Jikan and create record
                    record_type = self._extract_record_type(anime_element)
                    fetched_data = self._fetch_from_jikan(mal_id, record_type)
                    
                    if fetched_data:
                        master_record = self._create_master_record_from_jikan(mal_id, fetched_data, record_type)
                        master_record._is_new = True
                        self.db_session.add(master_record)
                        existing_mal_ids[mal_id] = master_record
                        new_records_created += 1
                    else:
                        # Create basic record from XML
                        master_record = self._create_basic_record_from_xml(anime_element, mal_id)
                        master_record._is_new = True
                        self.db_session.add(master_record)
                        existing_mal_ids[mal_id] = master_record
                        new_records_created += 1
                        
                except Exception as e:
                    error_msg = f"Failed to create record for anime {mal_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        # Flush to get IDs for new records
        try:
            if new_records_created > 0:
                logger.info(f"Saving {new_records_created} new records...")
                self.db_session.flush()
        except Exception as e:
            self.db_session.rollback()
            return ImportResult(False, f"Failed to save new records: {str(e)}")
        
        # STEP 4: Process user list items (much faster now - no more individual queries!)
        logger.info("Step 4: Processing user list items...")
        for anime, mal_id in anime_data:
            try:
                master_record = existing_mal_ids.get(mal_id)
                if not master_record:
                    skipped_count += 1
                    continue
                
                # Handle user list item
                result = self._handle_user_list_item(
                    anime, master_record, user_id, import_options
                )
                
                if result == 'imported':
                    imported_count += 1
                elif result == 'updated':
                    updated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                error_msg = f"Failed to process user list item for anime {mal_id}: {str(e)}"
                errors.append(error_msg)
                skipped_count += 1
                continue
        
        # Commit all changes
        try:
            logger.info("Committing all changes to database...")
            self.db_session.commit()
            logger.info("All changes committed successfully!")
        except Exception as e:
            self.db_session.rollback()
            return ImportResult(False, f"Failed to save changes: {str(e)}")
        
        # Build success message
        message = self._build_success_message(
            imported_count, updated_count, skipped_count,
            new_records_created, updated_records_count, errors
        )
        
        return ImportResult(
            success=True,
            message=message,
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            new_records_created=new_records_created,
            updated_records_count=updated_records_count,
            errors=errors
        )
    
    def _extract_mal_id(self, anime) -> Optional[int]:
        """Extract and validate MAL ID from anime element"""
        mal_id_elem = anime.find('series_animedb_id', self.namespace)
        if mal_id_elem is None or mal_id_elem.text is None:
            return None
        
        try:
            mal_id = int(mal_id_elem.text)
            if mal_id <= 0:
                return None
            return mal_id
        except (ValueError, TypeError):
            return None
    
    def _get_or_create_master_record(self, anime, mal_id: int) -> Optional[MasterRecord]:
        """Get existing master record or create new one"""
        # Check if record exists
        master_record = MasterRecord.query.filter_by(mal_id=mal_id).first()
        
        # Determine if we need to fetch data
        needs_data_fetch = (
            not master_record or
            not master_record.image_url or
            not master_record.synopsis or
            not master_record.source
        )
        
        if needs_data_fetch:
            # Fetch from Jikan API
            record_type = self._extract_record_type(anime)
            fetched_data = self._fetch_from_jikan(mal_id, record_type)
            
            if fetched_data:
                if not master_record:
                    # Create new record
                    master_record = self._create_master_record_from_jikan(mal_id, fetched_data, record_type)
                    master_record._is_new = True
                    self.db_session.add(master_record)
                else:
                    # Update existing record
                    self._update_master_record_from_jikan(master_record, fetched_data)
                    master_record._was_updated = True
                
                self.db_session.flush()  # Get ID
            elif not master_record:
                # Create basic record from XML
                master_record = self._create_basic_record_from_xml(anime, mal_id)
                master_record._is_new = True
                self.db_session.add(master_record)
                self.db_session.flush()
        
        return master_record
    
    def _extract_record_type(self, anime) -> str:
        """Extract record type from anime element"""
        record_type_elem = anime.find('series_type', self.namespace)
        if record_type_elem is not None and record_type_elem.text:
            return record_type_elem.text.lower()
        return 'anime'
    
    def _fetch_from_jikan(self, mal_id: int, record_type: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed data from Jikan API"""
        if record_type == 'manga':
            return self.jikan_client.fetch_manga(mal_id)
        else:
            return self.jikan_client.fetch_anime(mal_id)
    
    def _create_master_record_from_jikan(self, mal_id: int, data: Dict[str, Any], record_type: str) -> MasterRecord:
        """Create MasterRecord from Jikan API data"""
        return MasterRecord(
            mal_id=mal_id,
            original_title=data.get('title', ''),
            english_title=data.get('title_english', ''),
            record_type='Anime' if record_type == 'anime' else 'Manga',
            mal_type=data.get('type', ''),
            image_url=data.get('images', {}).get('jpg', {}).get('image_url', ''),
            synopsis=data.get('synopsis', ''),
            tags=", ".join([g.get('name', '') for g in data.get('genres', []) if g.get('name')]),
            themes=", ".join([t.get('name', '') for t in data.get('themes', []) if t.get('name')]),
            source=data.get('source', ''),
            studios=", ".join([s.get('name', '') for s in data.get('studios', []) if s.get('name')]) if record_type == 'anime' else '',
            release_year=data.get('year'),
            total_episodes=data.get('episodes') if record_type == 'anime' else data.get('chapters'),
            score=data.get('score'),
            popularity=data.get('popularity'),
            scored_by=data.get('scored_by'),
            status=data.get('status', ''),
            aired_from=self._parse_date_string(data.get('aired', {}).get('from') if record_type == 'anime' else data.get('published', {}).get('from')),
            aired_to=self._parse_date_string(data.get('aired', {}).get('to') if record_type == 'anime' else data.get('published', {}).get('to')),
            duration=data.get('duration', '') if record_type == 'anime' else '',
            demographics=", ".join([d.get('name', '') for d in data.get('demographics', []) if d.get('name')]),
            rating=data.get('rating', ''),
            members=data.get('members'),
            favorites=data.get('favorites'),
            relations=str(data.get('relations', [])),
            licensors=", ".join([l.get('name', '') for l in data.get('licensors', []) if l.get('name')]),
            producers=", ".join([p.get('name', '') for p in (data.get('producers', []) if record_type == 'anime' else data.get('authors', [])) if p.get('name')])
        )
    
    def _update_master_record_from_jikan(self, master_record: MasterRecord, data: Dict[str, Any]):
        """Update existing MasterRecord with Jikan API data"""
        master_record.image_url = data.get('images', {}).get('jpg', {}).get('image_url', '') or master_record.image_url
        master_record.synopsis = data.get('synopsis', '') or master_record.synopsis
        master_record.source = data.get('source', '') or master_record.source
        master_record.studios = data.get('studios', '') or master_record.studios
        master_record.demographics = ", ".join([d.get('name', '') for d in data.get('demographics', []) if d.get('name')]) or master_record.demographics
        master_record.tags = ", ".join([g.get('name', '') for g in data.get('genres', []) if g.get('name')]) or master_record.tags
        master_record.themes = ", ".join([t.get('name', '') for t in data.get('themes', []) if t.get('name')]) or master_record.themes
        master_record.english_title = data.get('title_english', '') or master_record.english_title
        master_record.mal_type = data.get('type', '') or master_record.mal_type
        master_record.release_year = data.get('year') or master_record.release_year
        master_record.total_episodes = data.get('episodes') or data.get('chapters') or master_record.total_episodes
        master_record.score = data.get('score') or master_record.score
        master_record.popularity = data.get('popularity') or master_record.popularity
        master_record.scored_by = data.get('scored_by') or master_record.scored_by
        master_record.status = data.get('status', '') or master_record.status
        master_record.aired_from = self._parse_date_string(data.get('aired', {}).get('from') or data.get('published', {}).get('from')) or master_record.aired_from
        master_record.aired_to = self._parse_date_string(data.get('aired', {}).get('to') or data.get('published', {}).get('to')) or master_record.aired_to
        master_record.duration = data.get('duration', '') or master_record.duration
        master_record.rating = data.get('rating', '') or master_record.rating
        master_record.members = data.get('members') or master_record.members
        master_record.favorites = data.get('favorites') or master_record.favorites
        master_record.relations = str(data.get('relations', [])) or master_record.relations
        master_record.licensors = ", ".join([l.get('name', '') for l in data.get('licensors', []) if l.get('name')]) or master_record.licensors
        master_record.producers = ", ".join([p.get('name', '') for p in (data.get('producers', []) if data.get('type') == 'anime' else data.get('authors', [])) if p.get('name')]) or master_record.producers
    
    def _create_basic_record_from_xml(self, anime, mal_id: int) -> MasterRecord:
        """Create basic MasterRecord from XML data when Jikan API fails"""
        title_elem = anime.find('series_title', self.namespace)
        title = title_elem.text if title_elem is not None else f"Unknown {mal_id}"
        
        record_type = self._extract_record_type(anime)
        
        episodes_elem = anime.find('series_episodes', self.namespace)
        total_episodes = None
        if episodes_elem is not None and episodes_elem.text and episodes_elem.text.isdigit():
            total_episodes = int(episodes_elem.text)
        
        return MasterRecord(
            mal_id=mal_id,
            original_title=title,
            record_type='Anime' if record_type == 'anime' else 'Manga',
            mal_type=record_type,
            total_episodes=total_episodes
        )
    
    def _parse_date_string(self, date_string: str) -> Optional[datetime]:
        """Parse date string from various formats"""
        if not date_string:
            return None
        try:
            if 'T' in date_string:
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_string, '%Y-%m-%d')
        except ValueError:
            return None
    
    def _handle_user_list_item(self, anime, master_record: MasterRecord, user_id: int, import_options: ImportOptions) -> str:
        """Handle individual user list item (create or update)"""
        # Check if item already exists in user's list
        existing_item = UserList.query.filter_by(
            user_id=user_id,
            master_record_id=master_record.id
        ).first()
        
        if existing_item:
            # Update existing item
            self._update_existing_item(existing_item, anime, master_record, import_options)
            return 'updated'
        else:
            # Create new item
            self._create_new_item(anime, master_record, user_id, import_options)
            return 'imported'
    
    def _update_existing_item(self, item: UserList, anime, master_record: MasterRecord, import_options: ImportOptions):
        """Update existing UserList item with new data"""
        if import_options.import_scores:
            score = self._extract_score(anime)
            if score is not None:
                item.user_score = score
        
        if import_options.import_notes:
            comments = self._extract_comments(anime)
            if comments:
                item.notes = comments
        
        if import_options.import_dates:
            self._update_item_status_and_progress(item, anime, master_record)
    
    def _create_new_item(self, anime, master_record: MasterRecord, user_id: int, import_options: ImportOptions):
        """Create new UserList item"""
        new_item = UserList(
            user_id=user_id,
            master_record_id=master_record.id,
            status='Planlandı',
            current_chapter=0,
            user_score=0,
            notes=''
        )
        
        # Set status and progress
        if import_options.import_dates:
            self._update_item_status_and_progress(new_item, anime, master_record)
        
        # Set score and notes
        if import_options.import_scores:
            score = self._extract_score(anime)
            if score is not None:
                new_item.user_score = score
        
        if import_options.import_notes:
            comments = self._extract_comments(anime)
            if comments:
                new_item.notes = comments
        
        self.db_session.add(new_item)
    
    def _extract_score(self, anime) -> Optional[int]:
        """Extract user score from anime element"""
        score_elem = anime.find('my_score', self.namespace)
        if score_elem is not None and score_elem.text and score_elem.text.isdigit():
            score = int(score_elem.text)
            if 1 <= score <= 10:
                return score
        return None
    
    def _extract_comments(self, anime) -> Optional[str]:
        """Extract user comments from anime element"""
        comments_elem = anime.find('my_comments', self.namespace)
        if comments_elem is not None and comments_elem.text:
            return comments_elem.text.strip()
        return None
    
    def _update_item_status_and_progress(self, item: UserList, anime, master_record: MasterRecord):
        """Update item status and progress based on MAL data"""
        status_elem = anime.find('my_status', self.namespace)
        if status_elem is not None and status_elem.text:
            mal_status = status_elem.text.lower()
            item.status = self._map_mal_status_to_local(mal_status)
            
            # Set progress based on status
            if mal_status == 'completed':
                item.current_chapter = master_record.total_episodes or 0
        
        # Update watched/read episodes
        progress_elem = anime.find('my_watched_episodes', self.namespace)
        if progress_elem is not None and progress_elem.text and progress_elem.text.isdigit():
            progress = int(progress_elem.text)
            if progress >= 0:
                item.current_chapter = progress
    
    def _map_mal_status_to_local(self, mal_status: str) -> str:
        """Map MAL status to local status"""
        status_mapping = {
            'completed': 'Tamamlandı',
            'watching': 'İzleniyor',
            'plan to watch': 'Planlandı',
            'on-hold': 'Bırakıldı',
            'dropped': 'Bırakıldı'
        }
        return status_mapping.get(mal_status, 'Planlandı')
    
    def _build_success_message(self, imported: int, updated: int, skipped: int, 
                              new_records: int, updated_records: int, errors: List[str]) -> str:
        """Build success message for import result"""
        message_parts = [
            f"Import completed! {imported} new items added, {updated} items updated, {skipped} items skipped."
        ]
        
        if new_records > 0:
            message_parts.append(f"{new_records} new anime/manga added to database.")
        
        if updated_records > 0:
            message_parts.append(f"{updated_records} existing anime/manga records updated.")
        
        if errors:
            message_parts.append(f"{len(errors)} errors occurred.")
        
        return " ".join(message_parts)
