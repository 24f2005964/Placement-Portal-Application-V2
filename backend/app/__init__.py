import os
from typing import Any, cast
from flask import Flask
from celery.schedules import crontab
from app.config import Config
from app.extensions import db, jwt, cors, cache, celery_app
from app.seed import seed_database

def make_celery(app):
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        beat_schedule={
            'send-daily-trek-reminders-every-day': {
                'task': 'tasks.send_daily_reminders',
                'schedule': crontab(hour=8, minute=0),  # Daily at 08:00 UTC
            },
            'generate-monthly-report': {
                'task': 'tasks.generate_monthly_report',
                'schedule': crontab(day_of_month=1, hour=0, minute=0),  # 1st of every month
            },
        }
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


def create_app(config_class=Config):
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/dist'))
    app = Flask(__name__, static_folder=os.path.join(frontend_dist, 'assets'), static_url_path='/assets')
    app.config.from_object(config_class)

    # Ensure export and upload folders exist
    os.makedirs(app.config.get('EXPORT_FOLDER', './exports'), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', './uploads'), exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(cast(Any, app), resources={r"/api/*": {"origins": "*"}})  # type: ignore[arg-type]
    cache.init_app(app)
    make_celery(app)

    # Register API Blueprints
    from app.api.auth import auth_bp
    from app.api.admin import admin_bp
    from app.api.staff import staff_bp
    from app.api.trekker import trekker_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(trekker_bp)

    # Serve compiled Vue SPA
    from flask import send_from_directory
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        if path.startswith('api/'):
            return {"error": "API route not found"}, 404
        if path != "" and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        if any(path.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.webp', '.woff', '.woff2', '.ttf', '.css', '.js', '.map')):
            return {"error": "Asset not found"}, 404
        return send_from_directory(frontend_dist, 'index.html')

    # Database Initialization & Programmatic Seeding
    with app.app_context():
        db.create_all()
        if not app.config.get('TESTING', False):
            seed_database()

    return app
