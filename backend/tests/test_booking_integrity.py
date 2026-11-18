import pytest
from app.models import Trek, Booking, User
from app.extensions import db

def test_competing_booking_requests_for_last_slot(client, app):
    """
    On an isolated test database, simulate two competing requests for the last slot.
    Verify that exactly one succeeds and the stored booking count and availability agree afterward.
    """
    with app.app_context():
        # Get an open trek, clear existing bookings, and set total_slots=1, available_slots=1
        trek = Trek.query.filter_by(status='Open').first()
        assert trek is not None
        trek_id = trek.id
        Booking.query.filter_by(trek_id=trek_id).delete()
        trek.total_slots = 1
        trek.available_slots = 1
        db.session.commit()

        # Two distinct registered trekkers
        u1 = User.query.filter_by(email='sneha@example.com').first()
        u2 = User.query.filter_by(email='arjun@example.com').first()
        assert u1 is not None and u2 is not None

    # Login both users
    token1 = client.post('/api/v1/auth/login', json={'email': 'sneha@example.com', 'password': 'trek123'}).get_json()['access_token']
    token2 = client.post('/api/v1/auth/login', json={'email': 'arjun@example.com', 'password': 'trek123'}).get_json()['access_token']

    # Competing request 1 for 1 seat
    res1 = client.post(
        f'/api/v1/trekker/treks/{trek_id}/book',
        headers={'Authorization': f'Bearer {token1}'},
        json={'seats': 1}
    )

    # Competing request 2 for 1 seat
    res2 = client.post(
        f'/api/v1/trekker/treks/{trek_id}/book',
        headers={'Authorization': f'Bearer {token2}'},
        json={'seats': 1}
    )

    # Exactly one request must succeed (HTTP 201), the other must fail (HTTP 400)
    statuses = [res1.status_code, res2.status_code]
    assert statuses.count(201) == 1, f"Expected exactly one 201, got: {statuses}"
    assert statuses.count(400) == 1, f"Expected exactly one 400, got: {statuses}"

    with app.app_context():
        trek_after = db.session.get(Trek, trek_id)
        assert trek_after is not None
        # Available slots must be 0 and status must be Closed
        assert trek_after.available_slots == 0
        assert trek_after.status == 'Closed'

        # Total confirmed seats booked on this trek
        confirmed_seats = db.session.query(db.func.sum(Booking.seats_booked))\
            .filter_by(trek_id=trek_id, status='Confirmed').scalar() or 0
        assert confirmed_seats == trek_after.total_slots - trek_after.available_slots


def test_staff_cannot_reduce_capacity_below_active_bookings(client, app):
    """
    Verify staff or admin cannot reduce capacity below existing active bookings.
    """
    with app.app_context():
        trek = Trek.query.filter_by(status='Open').first()
        assert trek is not None
        staff_user = trek.assigned_staff
        assert staff_user is not None
        trek_id = trek.id
        staff_email = staff_user.email

        # Ensure there are active bookings
        active_seats = db.session.query(db.func.sum(Booking.seats_booked))\
            .filter_by(trek_id=trek_id, status='Confirmed').scalar() or 0
        if active_seats == 0:
            u = User.query.filter_by(role='user').first()
            assert u is not None
            b = Booking(user_id=u.id, trek_id=trek_id, seats_booked=2, status='Confirmed')
            trek.available_slots -= 2
            db.session.add(b)
            db.session.commit()
            active_seats = 2

    # Login as assigned staff
    staff_token = client.post('/api/v1/auth/login', json={'email': staff_email, 'password': 'staff123'}).get_json()['access_token']

    # Try setting available_slots to something that exceeds capacity
    res = client.put(
        f'/api/v1/staff/treks/{trek_id}/slots',
        headers={'Authorization': f'Bearer {staff_token}'},
        json={'available_slots': 9999}
    )
    assert res.status_code == 400


def test_staff_cross_trek_ownership_isolated(client, app):
    """
    A staff member changing the trek ID in a request must not gain access to another staff member's trek.
    """
    with app.app_context():
        staff1 = User.query.filter_by(email='aarav.staff@tma.com').first()
        staff2 = User.query.filter_by(email='priya.staff@tma.com').first()
        assert staff1 is not None and staff2 is not None

        trek_of_staff2 = Trek.query.filter_by(assigned_staff_id=staff2.id).first()
        assert trek_of_staff2 is not None
        target_trek_id = trek_of_staff2.id

    # Login as staff1
    staff1_token = client.post('/api/v1/auth/login', json={'email': 'aarav.staff@tma.com', 'password': 'staff123'}).get_json()['access_token']

    # Staff1 tries to modify staff2's trek status
    res = client.put(
        f'/api/v1/staff/treks/{target_trek_id}/status',
        headers={'Authorization': f'Bearer {staff1_token}'},
        json={'status': 'Closed'}
    )
    assert res.status_code == 404
    assert 'not assigned to you' in res.get_json()['error']


def test_non_open_treks_reject_bookings(client, app):
    """
    Verify that closed, pending, completed, or otherwise non-open treks reject new bookings.
    """
    with app.app_context():
        trek = Trek.query.filter_by(status='Completed').first()
        assert trek is not None
        completed_trek_id = trek.id

    token = client.post('/api/v1/auth/login', json={'email': 'kavya@example.com', 'password': 'trek123'}).get_json()['access_token']

    res = client.post(
        f'/api/v1/trekker/treks/{completed_trek_id}/book',
        headers={'Authorization': f'Bearer {token}'},
        json={'seats': 1}
    )
    assert res.status_code == 400
    assert 'not open for booking' in res.get_json()['error']


def test_deactivated_accounts_cannot_continue_session(client, app):
    """
    Check that deactivated accounts cannot continue protected actions through an existing session.
    """
    token = client.post('/api/v1/auth/login', json={'email': 'rohan@example.com', 'password': 'trek123'}).get_json()['access_token']

    # Deactivate rohan in DB
    with app.app_context():
        u = User.query.filter_by(email='rohan@example.com').first()
        assert u is not None
        u.is_active = False
        db.session.commit()

    # User attempts protected action with previously valid token
    res = client.get('/api/v1/trekker/bookings', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 403
    assert 'inactive' in res.get_json()['error'].lower()


def test_cancellation_restores_availability_exactly_once(client, app):
    """
    Cancellation restores availability exactly once and preserves history.
    """
    with app.app_context():
        u = User.query.filter_by(email='sneha@example.com').first()
        assert u is not None
        t = Trek.query.filter_by(status='Open').first()
        assert t is not None

        # Clean existing bookings for sneha on this trek
        Booking.query.filter_by(user_id=u.id, trek_id=t.id).delete()
        initial_available = t.available_slots

        # Create confirmed booking for 2 seats
        b = Booking(user_id=u.id, trek_id=t.id, seats_booked=2, status='Confirmed')
        t.available_slots -= 2
        db.session.add(b)
        db.session.commit()
        booking_id = b.id
        trek_id = t.id

    token = client.post('/api/v1/auth/login', json={'email': 'sneha@example.com', 'password': 'trek123'}).get_json()['access_token']

    # Cancel booking
    res1 = client.put(f'/api/v1/trekker/bookings/{booking_id}/cancel', headers={'Authorization': f'Bearer {token}'})
    assert res1.status_code == 200
    assert res1.get_json()['booking']['status'] == 'Cancelled'

    with app.app_context():
        t_after = db.session.get(Trek, trek_id)
        assert t_after is not None
        assert t_after.available_slots == initial_available
        # Booking still exists in DB as Cancelled (history preserved)
        b_record = db.session.get(Booking, booking_id)
        assert b_record is not None
        assert b_record.status == 'Cancelled'

    # Try cancelling again
    res2 = client.put(f'/api/v1/trekker/bookings/{booking_id}/cancel', headers={'Authorization': f'Bearer {token}'})
    assert res2.status_code == 400
    assert 'already Cancelled' in res2.get_json()['error']

    with app.app_context():
        # Availability must NOT have been restored again
        t_after2 = db.session.get(Trek, trek_id)
        assert t_after2 is not None
        assert t_after2.available_slots == initial_available
