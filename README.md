# Trekking Management Application (TMA) - V2

A trekking expedition management web application built according to IITM BS Degree MAD 2 course specifications using Flask (REST API with Flask-JWT-Extended), Vue 3 SPA (Vite, Pinia, Vue Router, Bootstrap 5, Chart.js), SQLite (SQLAlchemy ORM), Redis (Caching), and Celery (Background Workers).

---

## System Architecture

```text
+-------------------------+          REST / JSON API          +-------------------------+
|   Vue 3 SPA (Vite)      | --------------------------------> |     Flask REST API      |
| (Pinia + Router + Chart)| <-------------------------------- |  (Flask-JWT-Extended)   |
+-------------------------+                                   +------------+------------+
                                                                           |
                                  +----------------------------------------+----------------------------------------+
                                  |                                        |                                        |
                                  v                                        v                                        v
                         +-----------------+                      +-----------------+                      +-----------------+
                         |   SQLite DB     |                      |   Redis Cache   |                      |  Celery Worker  |
                         |  (SQLAlchemy)   |                      |    & Broker     |                      |     + Beat      |
                         +-----------------+                      +-----------------+                      +-----------------+
```

---

## Project Directory Structure

```text
Trekking-Management-Application-V2/
├── README.md                           # Documentation and setup instructions
├── run.sh                              # Unified application startup script
├── requirements.txt                    # Python backend dependencies
│
├── backend/                            # Flask REST API, SQLite, Redis, Celery
│   ├── run.py                          # Flask API entrypoint (Port 5001)
│   ├── celery_worker.py                # Celery Worker entrypoint
│   ├── pytest.ini                      # Pytest configuration (pythonpath configured)
│   ├── tma_v2.db                       # SQLite database (auto-seeded on first run)
│   │
│   ├── app/                            # Flask application package
│   │   ├── __init__.py                 # Application factory, Blueprints, SPA serving
│   │   ├── config.py                   # Configuration and secret keys
│   │   ├── extensions.py               # Extensions (db, jwt, cors, cache, celery_app)
│   │   ├── models.py                   # User, StaffProfile, Trek, Booking models
│   │   ├── seed.py                     # Programmatic database seeder (Admin, Staff, Trekkers, Treks)
│   │   │
│   │   ├── api/                        # API Blueprints
│   │   │   ├── auth.py                 # Authentication (login, register, me, logout)
│   │   │   ├── admin.py                # Admin routes, staff approval, trek routes, reports
│   │   │   ├── staff.py                # Staff assigned treks, slot management, participants
│   │   │   └── trekker.py              # Trek discovery, booking, CSV export
│   │   │
│   │   ├── tasks/                      # Celery Background Jobs
│   │   │   ├── scheduled.py            # Daily trek reminders and monthly reports
│   │   │   └── export.py               # User-triggered async CSV export of booking history
│   │   │
│   │   ├── services/                   # Application services
│   │   │   ├── email_service.py        # Email dispatch and MIME archive logger
│   │   │   └── pdf_service.py          # Monthly activity report PDF generation
│   │   │
│   │   └── utils/                      # Utilities and decorators
│   │       ├── cache.py                # Redis cache invalidation helpers
│   │       └── decorators.py           # Role-based access control decorators
│   │
│   ├── exports/                        # Generated CSVs, reports, and reminder logs
│   └── tests/                          # Automated pytest suite (18/18 tests)
│
└── frontend/                           # Vue 3 SPA (Vite + Bootstrap 5)
    ├── index.html                      # Single page HTML entry
    ├── package.json                    # Frontend dependencies
    ├── vite.config.js                  # Vite configuration
    ├── dist/                           # Compiled production frontend build
    └── src/
        ├── App.vue                     # Root layout
        ├── main.js                     # Vue 3 initialization
        ├── router/index.js             # Route definitions with role-based auth guards
        ├── stores/auth.js              # Pinia auth store
        ├── services/api.js             # Axios client with JWT interceptors
        ├── components/                 # Reusable UI components
        └── views/                      # Role-specific views (Admin, Staff, Trekker, Auth)
```

---

## Quick Start & Run Instructions

### 1. Launch Application

```bash
bash run.sh
```

Or manually:

```bash
# 1. Start Redis
redis-server --daemonize yes

# 2. Start Celery Worker (from backend/)
cd backend
celery -A celery_worker worker --loglevel=info &

# 3. Start Flask Server (from backend/)
python3 run.py
```

The application is accessible at **http://127.0.0.1:5001**.

### 2. Default Accounts

| Role | Email | Password | Scope & Permissions |
|---|---|---|---|
| **Admin** | `admin@tma.com` | `admin123` | Master control: routes, staff approval, user management, reports |
| **Trek Staff** | `aarav.staff@tma.com` | `staff123` | Assigned expeditions, slot adjustment, participant rosters |
| **Trek Staff (Pending)** | `vikram.staff@tma.com` | `staff123` | Pending admin approval (login blocked until approved) |
| **Trekker** | `rohan@example.com` | `trek123` | Expedition discovery, booking, history, CSV export |

---

## Automated Testing

Run the full pytest suite:

```bash
cd backend
pytest -v
```

All 18 unit and integration tests cover Authentication, Role-Based Access Control, Booking Concurrency, Slot Constraints, Redis Caching, and Celery Jobs.
