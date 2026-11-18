import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.seed import seed_database

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_database()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    res = client.post('/api/v1/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
    return res.get_json()['access_token']

@pytest.fixture
def trekker_token(client):
    res = client.post('/api/v1/auth/login', json={'email': 'rohan@example.com', 'password': 'trek123'})
    return res.get_json()['access_token']

