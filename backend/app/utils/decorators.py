from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db
from app.models import User

def role_required(*allowed_roles):
    """
    Ensures user is authenticated with a valid JWT and matches one of the allowed roles.
    Also validates that the user account is active.
    """
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = db.session.get(User, int(user_id)) if user_id else None
            if not user or not user.is_active:
                return jsonify({'error': 'User account is inactive or disabled.'}), 403

            if user.role not in allowed_roles:
                return jsonify({'error': f'Access forbidden: requires role in {allowed_roles}'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    return role_required('admin')(fn)

def staff_required(fn):
    return role_required('staff', 'admin')(fn)

def approved_staff_required(fn):
    """
    Staff role required AND must be marked as is_approved by Admin.
    """
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id)) if user_id else None
        if not user or not user.is_active or user.role != 'staff':
            return jsonify({'error': 'Access forbidden: Staff role required.'}), 403

        if not user.is_approved:
            return jsonify({'error': 'Staff account pending Admin approval.'}), 403

        return fn(*args, **kwargs)
    return wrapper

def trekker_required(fn):
    return role_required('user')(fn)

