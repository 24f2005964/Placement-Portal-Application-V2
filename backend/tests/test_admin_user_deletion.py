def test_admin_delete_user_flow(client):
    # 1. Login as admin
    admin_login = client.post('/api/v1/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
    assert admin_login.status_code == 200
    token = admin_login.get_json()['access_token']
    admin_id = admin_login.get_json()['user']['id']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Prevent deleting self (admin)
    del_admin_res = client.delete(f'/api/v1/admin/users/{admin_id}', headers=headers)
    assert del_admin_res.status_code == 403
    assert 'Administrator account cannot be deleted' in del_admin_res.get_json()['error']

    # 3. Create a disposable trekker user
    reg_res = client.post('/api/v1/auth/register', json={
        'name': 'User To Delete',
        'email': 'delete_me@example.com',
        'password': 'password123',
        'role': 'user'
    })
    assert reg_res.status_code == 201
    user_id = reg_res.get_json()['user']['id']

    # 4. Successfully delete the user
    del_res = client.delete(f'/api/v1/admin/users/{user_id}', headers=headers)
    assert del_res.status_code == 200
    assert 'permanently deleted' in del_res.get_json()['message']

    # 5. Subsequent deletion should 404
    del_again_res = client.delete(f'/api/v1/admin/users/{user_id}', headers=headers)
    assert del_again_res.status_code == 404

