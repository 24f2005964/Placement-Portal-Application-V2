import json
import pytest
from app.models import User, Trek, Booking, UserNotification, ReminderConfig
from app.extensions import db
from app.services.email_service import dispatch_email_message


def test_trekker_notifications_inbox(app, client, trekker_token):
    headers = {'Authorization': f'Bearer {trekker_token}'}

    # Fetch rohan user
    user = User.query.filter_by(email='rohan@example.com').first()
    assert user is not None

    # Dispatch email notification to this user
    dispatch_res = dispatch_email_message(
        recipient_email=user.email,
        recipient_name=user.name,
        subject="Important Trek Gear Advisory",
        message="Please carry thermals and sturdy boots for tomorrow's trek.",
        user_id=user.id,
        trek_name="Kedarkantha Winter Summit",
        sender="TMA Operations"
    )
    assert dispatch_res['in_app_saved'] is True

    # Check trekker inbox
    inbox_res = client.get('/api/v1/trekker/notifications', headers=headers)
    assert inbox_res.status_code == 200
    inbox_data = inbox_res.get_json()
    assert inbox_data['unread_count'] >= 1
    assert any(n['subject'] == "Important Trek Gear Advisory" for n in inbox_data['notifications'])

    # Find the created notification ID
    target_notif = next(n for n in inbox_data['notifications'] if n['subject'] == "Important Trek Gear Advisory")
    notif_id = target_notif['id']

    # Mark as read
    read_res = client.put(f'/api/v1/trekker/notifications/{notif_id}/read', headers=headers)
    assert read_res.status_code == 200

    # Verify unread count decreased
    inbox_res_after = client.get('/api/v1/trekker/notifications', headers=headers)
    after_data = inbox_res_after.get_json()
    target_after = next(n for n in after_data['notifications'] if n['id'] == notif_id)
    assert target_after['is_read'] is True


def test_admin_sent_emails_and_smtp_config(app, client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}

    # Update reminder config with SMTP fields
    config_update_res = client.put('/api/v1/admin/reminders/config', json={
        'smtp_enabled': True,
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_user': 'testadmin@gmail.com',
        'smtp_pass': 'abcd efgh ijkl mnop',
        'smtp_from': 'TMA TrekSync <testadmin@gmail.com>'
    }, headers=headers)
    assert config_update_res.status_code == 200
    cfg = config_update_res.get_json()['config']
    assert cfg['smtp_enabled'] is True
    assert cfg['has_smtp_password'] is True

    # Dispatch a message to populate archive
    dispatch_email_message(
        recipient_email="test@example.com",
        recipient_name="Test Trekker",
        subject="Archived Email Test",
        message="This is a test to verify admin sent emails inspection."
    )

    # Check sent emails archive
    sent_res = client.get('/api/v1/admin/reminders/sent-emails', headers=headers)
    assert sent_res.status_code == 200
    sent_data = sent_res.get_json()
    assert 'emails' in sent_data
    assert len(sent_data['emails']) > 0

    # View email file content
    first_file = sent_data['emails'][0]['filename']
    detail_res = client.get(f'/api/v1/admin/reminders/sent-emails/{first_file}', headers=headers)
    assert detail_res.status_code == 200
    assert 'content' in detail_res.get_json()
