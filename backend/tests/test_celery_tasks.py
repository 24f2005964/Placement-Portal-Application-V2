from typing import Any, cast
from app.tasks.scheduled import send_daily_reminders, generate_monthly_report
from app.tasks.export import export_bookings_csv
from app.models import User

def test_daily_reminders_task(app):
    with app.app_context():
        result = send_daily_reminders()
        assert result['status'] == 'completed'
        assert 'reminders_sent' in result

def test_monthly_report_task(app):
    with app.app_context():
        result = generate_monthly_report()
        assert result['status'] == 'completed'
        assert 'report_file' in result

def test_export_bookings_csv_task(app):
    with app.app_context():
        user = User.query.filter_by(role='user').first()
        assert user is not None
        result = cast(Any, export_bookings_csv)(user.id)
        assert result['status'] == 'completed'
        assert result['record_count'] >= 0

