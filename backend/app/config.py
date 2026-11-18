import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tma-v2-super-secret-key-production-grade-2026-secure!')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tma-v2-jwt-secret-key-production-grade-2026-secure!')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_TOKEN_LOCATION = ['headers', 'query_string']
    JWT_QUERY_STRING_NAME = 'token'

    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'tma_v2.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis Config
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # Celery Config
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Export & Upload Storage
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CACHE_TYPE = 'NullCache'
    # Celery eager mode — tasks run synchronously inline (no worker needed for tests)
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_ALWAYS_EAGER = True          # Compatibility alias for older Celery versions
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

