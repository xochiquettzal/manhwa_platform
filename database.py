# database.py
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from models import db
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database manager with Flask app"""
        self.app = app
        
        # Configure database engine
        if app.config.get('TESTING'):
            # Use in-memory database for testing
            engine = create_engine(
                'sqlite:///:memory:',
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )
        else:
            # Use configured database URI
            engine = create_engine(
                app.config['SQLALCHEMY_DATABASE_URI'],
                pool_pre_ping=True,
                pool_recycle=300
            )
        
        # Create session factory
        self.session_factory = sessionmaker(bind=engine)
        self.Session = scoped_session(self.session_factory)
        
        # Setup database event listeners
        self._setup_event_listeners(engine)
        
        logger.info("Database manager initialized")
    
    def _setup_event_listeners(self, engine):
        """Setup database event listeners"""
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if "sqlite" in engine.url.drivername:
                # Enable foreign key constraints for SQLite
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            # Log slow queries
            conn.info.setdefault('query_start_time', []).append(conn.info.get('query_start_time', 0))
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            # Log query execution time
            total = conn.info.get('query_start_time', 0)
            if total > 1.0:  # Log queries taking more than 1 second
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query_func, *args, **kwargs):
        """Execute a database query with automatic session management"""
        with self.get_session() as session:
            return query_func(session, *args, **kwargs)
    
    def bulk_insert(self, model_class, objects):
        """Bulk insert objects into database"""
        with self.get_session() as session:
            try:
                session.bulk_insert_mappings(model_class, objects)
                session.commit()
                logger.info(f"Bulk inserted {len(objects)} {model_class.__name__} records")
                return True
            except Exception as e:
                logger.error(f"Bulk insert failed: {e}")
                session.rollback()
                return False
    
    def bulk_update(self, model_class, objects, update_fields):
        """Bulk update objects in database"""
        with self.get_session() as session:
            try:
                session.bulk_update_mappings(model_class, objects)
                session.commit()
                logger.info(f"Bulk updated {len(objects)} {model_class.__name__} records")
                return True
            except Exception as e:
                logger.error(f"Bulk update failed: {e}")
                session.rollback()
                return False
    
    def execute_raw_sql(self, sql, params=None):
        """Execute raw SQL query"""
        with self.get_session() as session:
            try:
                result = session.execute(sql, params or {})
                return result
            except Exception as e:
                logger.error(f"Raw SQL execution failed: {e}")
                raise
    
    def get_connection_info(self):
        """Get database connection information"""
        if not self.app:
            return {}
        
        db_uri = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if 'sqlite' in db_uri:
            return {
                'type': 'SQLite',
                'database': db_uri.split('/')[-1] if '/' in db_uri else 'memory'
            }
        elif 'postgresql' in db_uri:
            return {
                'type': 'PostgreSQL',
                'host': db_uri.split('@')[1].split('/')[0] if '@' in db_uri else 'unknown'
            }
        elif 'mysql' in db_uri:
            return {
                'type': 'MySQL',
                'host': db_uri.split('@')[1].split('/')[0] if '@' in db_uri else 'unknown'
            }
        else:
            return {'type': 'Unknown', 'uri': db_uri}

# Global database manager instance
db_manager = DatabaseManager()

def init_db(app):
    """Initialize database with Flask app"""
    db_manager.init_app(app)
    return db_manager

def get_db_session():
    """Get a database session"""
    return db_manager.Session()

@contextmanager
def db_session():
    """Context manager for database sessions"""
    with db_manager.get_session() as session:
        yield session
