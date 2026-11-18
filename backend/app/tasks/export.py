import os
import csv
from flask import current_app
from app.extensions import celery_app, db
from app.models import Booking, User

@celery_app.task(name='tasks.export_bookings_csv', bind=True)
def export_bookings_csv(self, user_id):
    """
    On-demand asynchronous task to export a user's trekking booking history as CSV.
    """
    user = db.session.get(User, user_id)
    if not user:
        return {'status': 'failed', 'error': 'User not found'}

    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.booking_date.desc()).all()

    export_folder = current_app.config.get('EXPORT_FOLDER', './exports')
    os.makedirs(export_folder, exist_ok=True)

    filename = f"bookings_export_{self.request.id}.csv"
    filepath = os.path.join(export_folder, filename)

    fieldnames = [
        'User ID',
        'Trekker Name',
        'Booking ID',
        'Trek Name',
        'Location',
        'Difficulty',
        'Duration (Days)',
        'Seats Booked',
        'Trek Start Date',
        'Trek End Date',
        'Booking Date',
        'Status'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for b in bookings:
            writer.writerow({
                'User ID': user.id,
                'Trekker Name': user.name,
                'Booking ID': b.id,
                'Trek Name': b.trek.name if b.trek else 'N/A',
                'Location': b.trek.location if b.trek else 'N/A',
                'Difficulty': b.trek.difficulty if b.trek else 'N/A',
                'Duration (Days)': b.trek.duration_days if b.trek else 'N/A',
                'Seats Booked': b.seats_booked,
                'Trek Start Date': b.trek.start_date.strftime('%Y-%m-%d') if (b.trek and b.trek.start_date) else 'N/A',
                'Trek End Date': b.trek.end_date.strftime('%Y-%m-%d') if (b.trek and b.trek.end_date) else 'N/A',
                'Booking Date': b.booking_date.strftime('%Y-%m-%d %H:%M:%S') if b.booking_date else 'N/A',
                'Status': b.status
            })

    return {
        'status': 'completed',
        'task_id': self.request.id,
        'filename': filename,
        'filepath': filepath,
        'record_count': len(bookings)
    }

