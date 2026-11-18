from app.models import Trek, User

def test_reminder_schedule_crud_and_dispatch(client):
    # 1. Login as Admin
    admin_login = client.post('/api/v1/auth/login', json={'email': 'admin@tma.com', 'password': 'admin123'})
    assert admin_login.status_code == 200
    token = admin_login.get_json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Get Reminder Config
    get_cfg = client.get('/api/v1/admin/reminders/config', headers=headers)
    assert get_cfg.status_code == 200
    cfg = get_cfg.get_json()['config']
    assert 'scheduled_time' in cfg
    assert 'days_before' in cfg

    # 3. Update / Edit the Schedule ('baad me bhi bhej sake / edit schedule')
    put_cfg = client.put('/api/v1/admin/reminders/config', json={
        'scheduled_time': '09:30',
        'days_before': 3,
        'channel': 'Email & Webhook',
        'webhook_url': 'https://chat.googleapis.com/v1/spaces/XYZ/messages',
        'is_active': True
    }, headers=headers)
    assert put_cfg.status_code == 200
    updated_cfg = put_cfg.get_json()['config']
    assert updated_cfg['scheduled_time'] == '09:30'
    assert updated_cfg['days_before'] == 3
    assert updated_cfg['webhook_url'] == 'https://chat.googleapis.com/v1/spaces/XYZ/messages'

    # 4. Instant Dispatch ('turant bhej sake')
    send_now = client.post('/api/v1/admin/reminders/send-now', headers=headers)
    assert send_now.status_code == 200
    assert 'completed' in send_now.get_json()['message'] or 'reminders_sent' in send_now.get_json()['details']

    # 5. Custom Notification Instant ('khud bhi bhej sake')
    custom_res = client.post('/api/v1/admin/reminders/custom', json={
        'subject': 'Trail Advisory: Waterproof Gear Required',
        'message': 'Rain forecast on the ridge. Please carry waterproof jackets and boots.',
        'channel': 'Email',
        'dispatch_type': 'Instant'
    }, headers=headers)
    assert custom_res.status_code == 200
    assert custom_res.get_json()['status'] == 'sent'

    # 6. Custom Notification Scheduled for Later ('baad me bhi bhej sake')
    sched_res = client.post('/api/v1/admin/reminders/custom', json={
        'subject': 'Final Departure Reminder',
        'message': 'Assemble at base camp 30 mins before sunrise.',
        'channel': 'Email',
        'dispatch_type': 'Scheduled Later',
        'scheduled_for': '2026-11-20 06:00'
    }, headers=headers)
    assert sched_res.status_code == 200
    assert sched_res.get_json()['status'] == 'scheduled'

    # 7. Check Notification Logs
    logs_res = client.get('/api/v1/admin/reminders/logs', headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.get_json()['logs']
    assert len(logs) >= 2

