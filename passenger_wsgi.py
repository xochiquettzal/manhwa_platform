import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
application = create_app()