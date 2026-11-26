import pytest
from learnplay.app import create_app, db, User, ServerSession, seed_demo_data, revoke_insecure_demo_sessions
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, timezone

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv('RENDER', raising=False)
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{tmp_path / "security.db"}', 'SESSION_COOKIE_SECURE': False, 'TRUST_PROXY_HOPS': 0})
    with app.app_context():
        db.create_all()
        seed_demo_data()
    yield app.test_client()
    with app.app_context():
        db.drop_all()

def csrf(client):
    return client.get('/api/v1/auth/csrf').json['csrf_token']

def test_auth_throttle_by_account(client):
    token = csrf(client)
    for _ in range(10):
        response = client.post('/api/v1/auth/login', json={'email':'unknown@example.com','password':'wrong'}, headers={'X-CSRF-Token':token})
        assert response.status_code == 401
    response = client.post('/api/v1/auth/login', json={'email':'unknown@example.com','password':'wrong'}, headers={'X-CSRF-Token':token})
    assert response.status_code == 429
    assert 1 <= int(response.headers['Retry-After']) <= 600

def test_malformed_json_body_and_request_limit(client):
    token = csrf(client)
    headers = {'X-CSRF-Token':token}
    assert client.post('/api/v1/auth/register', json=['invalid'], headers=headers).status_code == 422
    assert client.post('/api/v1/auth/register', json={'name': 'Test', 'email': 'test@example.com','password': 'x'*140000}, headers=headers).status_code == 413
    assert client.post('/api/v1/auth/register', json={'name':{},'email':'test@example.com','password':'long-test-password'}, headers=headers).status_code == 422

def test_api_headers(client):
    response = client.get('/api/v1/courses')
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert response.headers['Cache-Control'] == 'no-store'
    assert 'Cookie' in response.headers['Vary']

def test_public_default_denied_when_secure(client):
    client.application.config['SESSION_COOKIE_SECURE'] = True
    token = csrf(client)
    response = client.post('/api/v1/auth/login', json={'email':'admin@learnplay.local','password':'Admin123456!'}, headers={'X-CSRF-Token':token})
    assert response.status_code == 401

def test_seed_production_skips_public_passwords(tmp_path, monkeypatch):
    for key in ('DEMO_STUDENT_PASSWORD','DEMO_INSTRUCTOR_PASSWORD','DEMO_ADMIN_PASSWORD'):
        monkeypatch.delenv(key, raising=False)
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI':f'sqlite:///{tmp_path / "prod.db"}','SESSION_COOKIE_SECURE':True})
    with app.app_context():
        db.create_all()
        seed_demo_data()
        assert User.query.count() == 0
        db.drop_all()
