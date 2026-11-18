from datetime import datetime, timezone
from typing import Any
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(db.Model):
    """
    Unified User model representing all 3 platform roles:
    - 'admin': Platform administrator (pre-seeded, cannot self-register)
    - 'staff': Trek coordination staff (registered/added, requires approval)
    - 'user': Trekkers (self-register, search, and book treks)
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy='dynamic', foreign_keys='Trek.assigned_staff_id')
    notifications = db.relationship('UserNotification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'name': self.name,
            'phone': self.phone,
            'is_approved': self.is_approved,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'staff_profile': self.staff_profile.to_dict() if self.staff_profile else None
        }


class StaffProfile(db.Model):
    """
    Profile extension for Trek Staff members.
    """
    __tablename__ = 'staff_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(50), nullable=True)
    experience_years = db.Column(db.Integer, default=1)
    certification = db.Column(db.String(150), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bio': self.bio,
            'emergency_contact': self.emergency_contact,
            'experience_years': self.experience_years,
            'certification': self.certification
        }


class Trek(db.Model):
    __allow_unmapped__ = True
    """
    Trekking event model.
    Statuses: 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    Difficulties: 'Easy', 'Moderate', 'Hard'
    """
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False, default='Moderate')
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Open')
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationship to bookings
    bookings = db.relationship('Booking', backref='trek', lazy='dynamic', cascade='all, delete-orphan')
    assigned_staff: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'difficulty': self.difficulty,
            'duration_days': self.duration_days,
            'total_slots': self.total_slots,
            'available_slots': self.available_slots,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'status': self.status,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': self.assigned_staff.name if self.assigned_staff else 'Unassigned',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Booking(db.Model):
    __allow_unmapped__ = True
    """
    Trek reservation record for a user.
    Statuses: 'Confirmed', 'Cancelled', 'Completed'
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id', ondelete='CASCADE'), nullable=False, index=True)
    seats_booked = db.Column(db.Integer, nullable=False, default=1)
    booking_date = db.Column(db.DateTime, default=utc_now)
    status = db.Column(db.String(20), nullable=False, default='Confirmed')
    trek: Any = None
    user: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'trek_id': self.trek_id,
            'trek_name': self.trek.name if self.trek else 'Unknown Trek',
            'trek_location': self.trek.location if self.trek else '',
            'trek_difficulty': self.trek.difficulty if self.trek else '',
            'trek_start_date': self.trek.start_date.strftime('%Y-%m-%d') if (self.trek and self.trek.start_date) else None,
            'trek_end_date': self.trek.end_date.strftime('%Y-%m-%d') if (self.trek and self.trek.end_date) else None,
            'trek_status': self.trek.status if self.trek else 'Unknown',
            'user_name': self.user.name if self.user else 'Unknown Trekker',
            'user_email': self.user.email if self.user else '',
            'seats_booked': self.seats_booked,
            'booking_date': self.booking_date.strftime('%Y-%m-%d %H:%M:%S') if self.booking_date else None,
            'status': self.status
        }


class ReminderConfig(db.Model):
    __allow_unmapped__ = True
    __tablename__ = 'reminder_configs'

    id = db.Column(db.Integer, primary_key=True)
    scheduled_time = db.Column(db.String(10), default='08:00')       # HH:MM format (24h)
    days_before = db.Column(db.Integer, default=2)                   # Send N days before start date
    channel = db.Column(db.String(50), default='Email')              # 'Email', 'SMS'
    webhook_url = db.Column(db.String(500), nullable=True)          # Webhook URL (optional)
    is_active = db.Column(db.Boolean, default=True)                  # Enable / disable scheduled cron

    # Optional Live SMTP Settings for delivering to real inboxes (e.g. Gmail/Outlook)
    smtp_enabled = db.Column(db.Boolean, default=False)
    smtp_host = db.Column(db.String(120), nullable=True, default='smtp.gmail.com')
    smtp_port = db.Column(db.Integer, default=587)
    smtp_user = db.Column(db.String(120), nullable=True)
    smtp_pass = db.Column(db.String(120), nullable=True)
    smtp_from = db.Column(db.String(120), nullable=True, default='TMA TrekSync <noreply@tma.com>')

    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        valid_channel = self.channel if self.channel in ['Email', 'SMS'] else 'Email'
        return {
            'id': self.id,
            'scheduled_time': self.scheduled_time or '08:00',
            'days_before': self.days_before or 2,
            'channel': valid_channel,
            'webhook_url': self.webhook_url or '',
            'is_active': bool(self.is_active),
            'smtp_enabled': bool(self.smtp_enabled),
            'smtp_host': self.smtp_host or '',
            'smtp_port': self.smtp_port or 587,
            'smtp_user': self.smtp_user or '',
            'smtp_from': self.smtp_from or '',
            'has_smtp_password': bool(self.smtp_pass),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class NotificationLog(db.Model):
    __allow_unmapped__ = True
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id', ondelete='SET NULL'), nullable=True)
    trek_name = db.Column(db.String(120), nullable=False)
    recipient_count = db.Column(db.Integer, default=0)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(50), default='Email')
    dispatch_type = db.Column(db.String(30), default='Instant')      # 'Instant', 'Scheduled Later', 'Automated Daily'
    scheduled_for = db.Column(db.String(30), nullable=True)          # Scheduled execution time
    status = db.Column(db.String(20), default='Sent')                # 'Sent', 'Scheduled', 'Failed'
    sent_by = db.Column(db.String(100), default='System Admin')
    created_at = db.Column(db.DateTime, default=utc_now)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'trek_id': self.trek_id,
            'trek_name': self.trek_name,
            'recipient_count': self.recipient_count,
            'subject': self.subject,
            'message': self.message,
            'channel': self.channel,
            'dispatch_type': self.dispatch_type,
            'scheduled_for': self.scheduled_for,
            'status': self.status,
            'sent_by': self.sent_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class UserNotification(db.Model):
    __allow_unmapped__ = True
    __tablename__ = 'user_notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = db.Column(db.String(100), default='TMA Operations')
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    trek_name = db.Column(db.String(120), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender': self.sender,
            'subject': self.subject,
            'message': self.message,
            'trek_name': self.trek_name or '',
            'is_read': bool(self.is_read),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


