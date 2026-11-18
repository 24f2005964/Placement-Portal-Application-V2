import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, celery_app
import app.tasks.scheduled
import app.tasks.export

flask_app = create_app()
flask_app.app_context().push()

if __name__ == '__main__':
    celery_app.start()

