from datetime import date, timedelta
from app.extensions import db
from app.models import User, StaffProfile, Trek, Booking

def seed_database():
    """
    Populates database with default Admin, Staff, Trekkers, and Treks if empty.
    Matches all assignment requirements.
    """
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        default_admin = User(
            name='System Administrator',
            email='admin@tma.com',
            role='admin',
            phone='9876543210',
            is_approved=True,
            is_active=True
        )
        default_admin.set_password('admin123')
        db.session.add(default_admin)
        db.session.commit()
        print(">>> [SEED] Default Admin seeded: admin@tma.com / admin123")

    if Trek.query.count() == 0:
        # Create Staff
        s1 = User(name='Aarav Mehta', email='aarav.staff@tma.com', role='staff', phone='9811122233', is_approved=True, is_active=True)
        s1.set_password('staff123')
        p1 = StaffProfile(user=s1, bio='Senior Himalayan guide with 8 years experience.', emergency_contact='9811122299', experience_years=8, certification='IMF Certified')

        s2 = User(name='Priya Sharma', email='priya.staff@tma.com', role='staff', phone='9822233344', is_approved=True, is_active=True)
        s2.set_password('staff123')
        p2 = StaffProfile(user=s2, bio='Wilderness first responder and Western Ghats expert.', emergency_contact='9822233399', experience_years=5, certification='WFR & Mountaineering')

        s3 = User(name='Vikram Negi', email='vikram.staff@tma.com', role='staff', phone='9833344455', is_approved=False, is_active=True)
        s3.set_password('staff123')
        p3 = StaffProfile(user=s3, bio='Pending staff applicant.', emergency_contact='9833344499', experience_years=2, certification='Basic Mountaineering')

        # Create Trekkers
        u1 = User(name='Rohan Sharma', email='rohan@example.com', role='user', phone='9871112233', is_approved=True, is_active=True)
        u1.set_password('trek123')

        u2 = User(name='Sneha Patel', email='sneha@example.com', role='user', phone='9872223344', is_approved=True, is_active=True)
        u2.set_password('trek123')

        u3 = User(name='Arjun Verma', email='arjun@example.com', role='user', phone='9873334455', is_approved=True, is_active=True)
        u3.set_password('trek123')

        u4 = User(name='Kavya Nair', email='kavya@example.com', role='user', phone='9874445566', is_approved=True, is_active=True)
        u4.set_password('trek123')

        db.session.add_all([s1, p1, s2, p2, s3, p3, u1, u2, u3, u4])
        db.session.commit()

        # Create Treks
        today = date.today()
        treks = [
            Trek(
                name='Roopkund Mystery Lake Trek',
                description='High altitude glacial lake trek in Uttarakhand famous for hundreds of ancient human skeletons.',
                location='Uttarakhand, Himalayas',
                difficulty='Hard',
                duration_days=8,
                total_slots=20,
                available_slots=17,
                start_date=today + timedelta(days=1),  # Starts tomorrow (triggers daily reminder)
                end_date=today + timedelta(days=9),
                status='Open',
                assigned_staff_id=s1.id
            ),
            Trek(
                name='Valley of Flowers & Hemkund Sahib',
                description='UNESCO World Heritage site known for meadows of endemic alpine flowers and diverse fauna.',
                location='Chamoli, Uttarakhand',
                difficulty='Moderate',
                duration_days=6,
                total_slots=25,
                available_slots=23,
                start_date=today + timedelta(days=5),
                end_date=today + timedelta(days=11),
                status='Open',
                assigned_staff_id=s1.id
            ),
            Trek(
                name='Kedarkantha Winter Summit',
                description='Popular winter snow trek offering 360-degree views of prominent Himalayan mountain peaks.',
                location='Uttarkashi, Uttarakhand',
                difficulty='Easy',
                duration_days=5,
                total_slots=30,
                available_slots=28,
                start_date=today + timedelta(days=10),
                end_date=today + timedelta(days=15),
                status='Open',
                assigned_staff_id=s2.id
            ),
            Trek(
                name='Hampta Pass & Chandratal Lake',
                description='Dramatic crossover trek from the lush green valleys of Kullu to the stark arid landscape of Spiti.',
                location='Manali, Himachal Pradesh',
                difficulty='Moderate',
                duration_days=5,
                total_slots=18,
                available_slots=18,
                start_date=today + timedelta(days=14),
                end_date=today + timedelta(days=19),
                status='Open',
                assigned_staff_id=s2.id
            ),
            Trek(
                name='Har Ki Dun Valley of Gods',
                description='Ancient cradle-shaped hanging valley nestled amidst untouched alpine vegetation and glaciers.',
                location='Garhwal, Uttarakhand',
                difficulty='Moderate',
                duration_days=7,
                total_slots=22,
                available_slots=22,
                start_date=today + timedelta(days=20),
                end_date=today + timedelta(days=27),
                status='Open',
                assigned_staff_id=s1.id
            ),
            Trek(
                name='Kudremukh Peak Rainforest Trail',
                description='Scenic horse-face peak trail through lush shola grasslands and dense rainforests in the Western Ghats.',
                location='Chikkamagaluru, Karnataka',
                difficulty='Moderate',
                duration_days=2,
                total_slots=25,
                available_slots=25,
                start_date=today + timedelta(days=3),
                end_date=today + timedelta(days=5),
                status='Open',
                assigned_staff_id=s2.id
            ),
            Trek(
                name='Triund Panoramic Ridge Walk',
                description='Charming short trek in the lap of the Dhauladhar range overlooking Kangra valley.',
                location='Dharamshala, Himachal Pradesh',
                difficulty='Easy',
                duration_days=2,
                total_slots=40,
                available_slots=40,
                start_date=today + timedelta(days=7),
                end_date=today + timedelta(days=9),
                status='Open',
                assigned_staff_id=None
            ),
            Trek(
                name='Bhrigu Lake High Altitude Alpine Trail',
                description='Sacred alpine lake located at an elevation of 14,100 ft that never completely freezes.',
                location='Manali, Himachal Pradesh',
                difficulty='Moderate',
                duration_days=4,
                total_slots=15,
                available_slots=0,
                start_date=today - timedelta(days=20),
                end_date=today - timedelta(days=16),
                status='Completed',
                assigned_staff_id=s1.id
            )
        ]

        db.session.add_all(treks)
        db.session.commit()

        # Seed initial bookings
        b1 = Booking(user_id=u1.id, trek_id=treks[0].id, seats_booked=2, status='Confirmed')
        b2 = Booking(user_id=u2.id, trek_id=treks[0].id, seats_booked=1, status='Confirmed')
        b3 = Booking(user_id=u3.id, trek_id=treks[1].id, seats_booked=2, status='Confirmed')
        b4 = Booking(user_id=u1.id, trek_id=treks[2].id, seats_booked=2, status='Confirmed')
        b5 = Booking(user_id=u4.id, trek_id=treks[7].id, seats_booked=1, status='Completed')

        db.session.add_all([b1, b2, b3, b4, b5])
        db.session.commit()
        print(">>> [SEED] Database seeded with 10 users, 8 treks, and 5 bookings.")

