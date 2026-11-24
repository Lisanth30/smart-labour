# Urban Service Management System

A premium web-based platform to manage home services with Tamil Nadu city-wise worker allocation.

## Features
- **Multi-role Access**: Integrated dashboards for Admin, Workers, and Customers.
- **Service Booking**: Book Electricians, Plumbers, Cleaners, etc., with specific date/time slots.
- **Tamil Nadu Specific**: City and Area based worker allocation system.
- **Priority Handling**: Emergency service prioritization for urgent tasks.
- **Real-time Tracking**: Live status updates from 'Requested' to 'Completed'.
- **Feedback System**: Customers can rate and review services.
- **Premium UI**: Modern, responsive design with glassmorphism and smooth animations.

## Tech Stack
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript
- **Backend**: Python (Flask)
- **Database**: PostgreSQL (via `psycopg2` and connection pooling)

## Setup Instructions
1. **Database Setup**:
   - Ensure PostgreSQL is running (default database: `postgres` or set custom `DB_NAME` in environment variables).
   - Edit `db_config.py` (or set the `DB_*` environment variables) with your PostgreSQL credentials.
   - You can test connectivity from the command line:
     ```bash
     python urban/test_db.py
     ```
   - To recreate the schema use the `schema.sql` script via `psql` or your GUI of choice.

2. **Install Dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   python app.py
   ```
   Access at: `http://localhost:5000`

## Project Structure
```
urban/                   # Python package root
├── __init__.py          # application factory (optional)
├── app.py               # entry point & route definitions
├── db_config.py         # psycopg2 connection helpers (pool, context manager)
├── models.py            # dataclasses / simple models
├── test_db.py           # quick script to verify connectivity
├── schema.sql           # PostgreSQL schema and seed data
├── templates/           # Jinja2 templates (index.html, users.html, ...)
└── static/              # CSS and other static assets
```

Use `app.py` to run the server (`python urban/app.py`).
