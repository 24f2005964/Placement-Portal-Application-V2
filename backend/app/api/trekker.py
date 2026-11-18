import os
import csv
from typing import Any, cast
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db, cache
from app.models import User, Trek, Booking, UserNotification
from app.utils.decorators import trekker_required
from app.utils.cache import invalidate_treks_cache, invalidate_dashboard_cache
from app.tasks.export import export_bookings_csv

trekker_bp = Blueprint('trekker', __name__, url_prefix='/api/v1/trekker')

def _get_current_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if user is None:
        raise ValueError("Authenticated user not found.")
    return user


@trekker_bp.route('/dashboard', methods=['GET'])
@trekker_required
def dashboard():
    user = _get_current_user()
    bookings = Booking.query.filter_by(user_id=user.id).all()

    total_bookings = len(bookings)
    confirmed_bookings = sum(1 for b in bookings if b.status == 'Confirmed')
    completed_treks = sum(1 for b in bookings if b.status == 'Completed')
    cancelled_bookings = sum(1 for b in bookings if b.status == 'Cancelled')

    return jsonify({
        'profile': user.to_dict(),
        'counts': {
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'completed_treks': completed_treks,
            'cancelled_bookings': cancelled_bookings
        }
    }), 200


@trekker_bp.route('/treks', methods=['GET'])
@jwt_required(optional=True)
def get_open_treks():
    search = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()

    # Generate cache key
    cache_key = f"cache:treks:s={search}:d={difficulty}:l={location}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        response = jsonify(cached_data)
        response.headers['X-Cache'] = 'HIT'
        return response, 200

    query = Trek.query.filter(Trek.status.in_(['Open', 'Approved']))

    if search:
        search_pat = f"%{search}%"
        query = query.filter(db.or_(Trek.name.ilike(search_pat), Trek.location.ilike(search_pat)))
    if difficulty and difficulty != 'All':
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    treks = query.order_by(Trek.start_date.asc()).all()
    payload = {'count': len(treks), 'treks': [t.to_dict() for t in treks]}

    # Cache for 300 seconds
    cache.set(cache_key, payload, timeout=300)

    response = jsonify(payload)
    response.headers['X-Cache'] = 'MISS'
    return response, 200


@trekker_bp.route('/treks/<int:trek_id>/book', methods=['POST'])
@trekker_required
def book_trek(trek_id):
    user = _get_current_user()
    data = request.get_json() or {}
    seats = int(data.get('seats', 1))

    if seats < 1:
        return jsonify({'error': 'You must book at least 1 seat.'}), 400

    # 1. Fetch trek
    trek = db.session.get(Trek, trek_id)
    if not trek:
        return jsonify({'error': 'Trek not found.'}), 404

    # 2. Check trek status
    if trek.status != 'Open':
        return jsonify({'error': f'This trek is not open for booking (status: {trek.status}).'}), 400

    # 3. Check for existing active booking
    existing = Booking.query.filter_by(user_id=user.id, trek_id=trek.id, status='Confirmed').first()
    if existing:
        return jsonify({'error': 'You already have an active confirmed reservation for this trek.'}), 409

    # 4. Check available slots
    if seats > trek.available_slots:
        return jsonify({
            'error': f'Cannot book {seats} seat(s). Only {trek.available_slots} seat(s) available.',
            'available_slots': trek.available_slots
        }), 400

    # 5. Atomic Booking + Slot decrement
    try:
        trek.available_slots -= seats
        if trek.available_slots == 0:
            trek.status = 'Closed'

        booking = Booking(
            user_id=user.id,
            trek_id=trek.id,
            seats_booked=seats,
            status='Confirmed'
        )

        db.session.add(booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Booking failed due to a database error.'}), 500

    invalidate_treks_cache()
    invalidate_dashboard_cache()

    return jsonify({
        'message': f'Booking confirmed for {trek.name} ({seats} seat(s)).',
        'booking': booking.to_dict(),
        'available_slots': trek.available_slots
    }), 201


@trekker_bp.route('/bookings', methods=['GET'])
@trekker_required
def get_my_bookings():
    user = _get_current_user()
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.booking_date.desc()).all()
    return jsonify({'bookings': [b.to_dict() for b in bookings]}), 200


@trekker_bp.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
@trekker_required
def cancel_booking(booking_id):
    user = _get_current_user()
    booking = Booking.query.filter_by(id=booking_id, user_id=user.id).first()

    if not booking:
        return jsonify({'error': 'Booking not found.'}), 404

    if booking.status != 'Confirmed':
        return jsonify({'error': f'Cannot cancel a booking that is already {booking.status}.'}), 400

    # Restore seats
    trek = booking.trek
    booking.status = 'Cancelled'
    if trek:
        trek.available_slots = min(trek.total_slots, trek.available_slots + booking.seats_booked)
        if trek.status == 'Closed' and trek.available_slots > 0:
            trek.status = 'Open'

    db.session.commit()
    invalidate_treks_cache()
    invalidate_dashboard_cache()

    return jsonify({
        'message': f'Booking #{booking.id} has been cancelled and seats released.',
        'booking': booking.to_dict()
    }), 200


@trekker_bp.route('/profile', methods=['GET'])
@trekker_required
def get_profile():
    user = _get_current_user()
    return jsonify({'user': user.to_dict()}), 200


@trekker_bp.route('/profile', methods=['PUT'])
@trekker_required
def update_profile():
    user = _get_current_user()
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')

    if name:
        user.name = name
    if phone:
        user.phone = phone

    if new_password:
        if not current_password or not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect.'}), 400
        user.set_password(new_password)

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully.', 'user': user.to_dict()}), 200


@trekker_bp.route('/bookings/export', methods=['POST'])
@trekker_required
def export_bookings():
    """
    Submits Celery batch job to export the user's booking history as CSV.
    """
    user = _get_current_user()
    task = cast(Any, export_bookings_csv).delay(user.id)
    return jsonify({
        'message': 'Booking history CSV export job queued.',
        'task_id': task.id
    }), 202


@trekker_bp.route('/exports/<task_id>/download', methods=['GET'])
@trekker_required
def download_export(task_id):
    """
    Downloads exported CSV. If task ran or if worker was offline, generates file directly on-the-fly!
    """
    user = _get_current_user()
    filename = f"bookings_export_{task_id}.csv"
    export_folder = current_app.config['EXPORT_FOLDER']
    os.makedirs(export_folder, exist_ok=True)
    file_path = os.path.join(export_folder, filename)

    if not os.path.exists(file_path):
        bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.booking_date.desc()).all()
        fieldnames = ['User ID', 'Trekker Name', 'Booking ID', 'Trek Name', 'Location', 'Difficulty', 'Duration (Days)', 'Seats Booked', 'Trek Start Date', 'Trek End Date', 'Booking Date', 'Status']
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
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

    return send_from_directory(export_folder, filename, as_attachment=True)


# =============================================================================
# IN-APP EMAIL & NOTIFICATIONS INBOX
# =============================================================================

@trekker_bp.route('/notifications', methods=['GET'])
@trekker_required
def get_user_notifications():
    """
    In-app Email / Notifications Inbox for the logged-in trekker.
    """
    user = _get_current_user()
    notifications = UserNotification.query.filter_by(user_id=user.id).order_by(UserNotification.created_at.desc()).all()
    unread_count = sum(1 for n in notifications if not n.is_read)
    return jsonify({
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifications]
    }), 200


@trekker_bp.route('/notifications/<int:notif_id>/read', methods=['PUT'])
@trekker_required
def mark_notification_as_read(notif_id):
    """
    Mark an individual notification as read.
    """
    user = _get_current_user()
    notif = db.session.get(UserNotification, notif_id)
    if not notif or notif.user_id != user.id:
        return jsonify({'error': 'Notification not found.'}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notification marked as read.', 'notification': notif.to_dict()}), 200


@trekker_bp.route('/notifications/read-all', methods=['PUT'])
@trekker_required
def mark_all_notifications_read():
    """
    Mark all notifications as read for the logged-in trekker.
    """
    user = _get_current_user()
    UserNotification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read.'}), 200

