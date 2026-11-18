def test_admin_login(client):
    res = client.post('/api/v1/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
    assert res.status_code == 200
    assert 'access_token' in res.get_json()
    assert res.get_json()['user']['role'] == 'admin'

def test_invalid_login(client):
    res = client.post('/api/v1/auth/login', json={'email': 'admin@tma.com', 'password': 'wrong'})
    assert res.status_code == 401

def test_trekker_registration_and_login(client):
    res = client.post('/api/v1/auth/register', json={
        'name': 'New Trekker',
        'email': 'newtrekker@example.com',
        'password': 'password123',
        'role': 'user'
    })
    assert res.status_code == 201

    login_res = client.post('/api/v1/auth/login', json={
        'email': 'newtrekker@example.com',
        'password': 'password123'
    })
    assert login_res.status_code == 200

def test_pending_staff_login_blocked(client):
    res = client.post('/api/v1/auth/login', json={'email': 'vikram.staff@tma.com', 'password': 'staff123'})
    assert res.status_code == 403

