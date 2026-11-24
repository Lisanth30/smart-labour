from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db_config import get_db_connection, return_db_connection, db_cursor
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'urban_key_123'
bcrypt = Bcrypt(app)

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']
        role = request.form['role']
        
        db = get_db_connection()
        if not db:
            flash("Could not connect to the database. Please ensure PostgreSQL/pgAdmin is running.", "danger")
            return render_template('login.html')
            
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        if role == 'admin':
            cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        elif role == 'worker':
            cursor.execute("SELECT * FROM workers WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
            
        user = cursor.fetchone()
        return_db_connection(db)
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = role
            session['name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for(f'{role}_dashboard'))
        else:
            flash("Invalid credentials or role. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower().strip()
        password = request.form['password']
        phone = request.form['phone']
        role = request.form.get('role', 'customer')
        
        db = get_db_connection()
        if not db:
            flash("Could not connect to the database. Please ensure PostgreSQL/pgAdmin is running.", "danger")
            return redirect(url_for('register'))
            
        cursor = db.cursor()
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        
        try:
            if role == 'customer':
                city_id = request.form['city']
                area_id = request.form['area']
                address = request.form['address']
                cursor.execute("""
                    INSERT INTO customers (full_name, email, password, phone, address, city_id, area_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, email, hashed_pw, phone, address, city_id, area_id))
            elif role == 'worker':
                service_id = request.form['service']
                city_id = request.form['city']
                cursor.execute("""
                    INSERT INTO workers (full_name, email, password, phone, service_id, city_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, email, hashed_pw, phone, service_id, city_id))
                
            db.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            return_db_connection(db)
            
    # GET data for dropdowns
    db = get_db_connection()
    if not db:
        flash("Could not connect to the database. Please ensure PostgreSQL/pgAdmin is running.", "danger")
        return render_template('register.html', cities=[], services=[])
        
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM cities")
    cities = cursor.fetchall()
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    return_db_connection(db)
    
    return render_template('register.html', cities=cities, services=services)

@app.route('/get_areas/<city_id>')
def get_areas(city_id):
    db = get_db_connection()
    if not db:
        return jsonify([])
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM areas WHERE city_id = %s", (city_id,))
    areas = cursor.fetchall()
    return_db_connection(db)
    return jsonify(areas)


# -------- simple demo route -------------------------------------------------
@app.route('/users')
def list_users():
    """Show all customers (a stand‑in for a "users" table)."""
    # using the context‑manager (it handles commit/close automatically)
    with db_cursor() as cur:
        cur.execute("SELECT id, full_name, email FROM customers ORDER BY id")
        users = cur.fetchall()
    return render_template('users.html', users=users)

@app.route('/admin/add_worker', methods=['POST'])
def add_worker():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']
    service_id = request.form['service']
    city_id = request.form['city']
    
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('admin_dashboard'))
    cursor = db.cursor()
    
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    
    try:
        cursor.execute("""
            INSERT INTO workers (full_name, email, password, phone, service_id, city_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, hashed_pw, phone, service_id, city_id))
        db.commit()
        flash("Worker added successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# --- Dashboards ---

@app.route('/customer/dashboard')
def customer_dashboard():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('index'))
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Get services for booking
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    
    # Get user details
    cursor.execute("SELECT * FROM customers WHERE id = %s", (session['user_id'],))
    user_details = cursor.fetchone()
    
    # Get cities for booking
    cursor.execute("SELECT * FROM cities")
    cities = cursor.fetchall()
    
    # Get my requests with worker details and ETA
    cursor.execute("""
        SELECT sr.*, s.name as service_name, city.name as city_name, a_area.name as area_name,
               w.full_name as worker_name, w.phone as worker_phone, w.rating_avg, w.jobs_completed, w.bio as worker_bio,
               asgn.eta, asgn.started_at,
               (SELECT COUNT(*) FROM customer_favorites cf WHERE cf.customer_id = %s AND cf.worker_id = w.id) > 0 as is_favorite
        FROM service_requests sr
        JOIN services s ON sr.service_id = s.id
        JOIN cities city ON sr.city_id = city.id
        JOIN areas a_area ON sr.area_id = a_area.id
        LEFT JOIN assignments asgn ON sr.id = asgn.request_id
        LEFT JOIN workers w ON asgn.worker_id = w.id
        WHERE sr.customer_id = %s
        ORDER BY sr.created_at DESC
    """, (session['user_id'], session['user_id']))
    all_requests = cursor.fetchall()

    # Filter out requests that need payment
    pending_payments = [r for r in all_requests if r['status'] == 'Completed' and r['payment_status'] == 'Pending Approval']
    
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return_db_connection(db)
    return render_template('customer_dashboard.html', 
                          user=user_details, 
                          services=services, 
                          cities=cities, 
                          requests=all_requests, 
                          pending_payments=pending_payments,
                          current_date=current_date)

@app.route('/book_service', methods=['POST'])
def book_service():
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.form
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('customer_dashboard'))
    cursor = db.cursor()
    
    try:
        # 1. Fetch base price for the service
        cursor.execute("SELECT base_price FROM services WHERE id = %s", (data['service_id'],))
        base_price = cursor.fetchone()[0]

        # 2. Insert the request with service fee
        cursor.execute("""
            INSERT INTO service_requests (customer_id, service_id, city_id, area_id, request_date, time_slot, description, status, service_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Requested', %s)
            RETURNING id
        """, (session['user_id'], data['service_id'], data['city_id'], data['area_id'], data['date'], data['time_slot'], data['description'], base_price))
        
        result = cursor.fetchone()
        request_id = result[0]
        
        # 2. Automation: Find Available Worker
        # Priority 1: Match same Area and same Skill
        cursor.execute("""
            SELECT id FROM workers 
            WHERE service_id = %s AND city_id = %s AND status = 'Available'
            ORDER BY CASE WHEN city_id = %s THEN 0 ELSE 1 END ASC
            LIMIT 1
        """, (data['service_id'], data['city_id'], data['city_id']))
        
        # Note: In our current schema, workers are linked to cities (districts). 
        # To be even more precise, we check match in the same city.
        
        worker = cursor.fetchone()
        
        if worker:
            worker_id = worker['id'] if isinstance(worker, dict) else worker[0]
            # Auto-assign (But wait for presence confirmation if we want to follow the prompt strictly)
            # Actually, "Before dispatching a worker, system asks customer to confirm availability"
            # So we can assign him, but worker shouldn't 'dispatch' until confirmed.
            # For now, let's keep it simple: auto-assign and set status to 'Assigned'.
            cursor.execute("UPDATE service_requests SET status = 'Assigned' WHERE id = %s", (request_id,))
            cursor.execute("INSERT INTO assignments (request_id, worker_id) VALUES (%s, %s)", (request_id, worker_id))
            cursor.execute("UPDATE workers SET status = 'Busy' WHERE id = %s", (worker_id,))
            flash("Smart Match: A specialist in your district has been automatically assigned! Please confirm your availability in the dashboard.", "success")
        else:
            flash("Request Received: We are checking for available workers in your area.", "info")

        db.commit()
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
        
    return redirect(url_for('customer_dashboard'))

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    
    db = get_db_connection()
    if not db:
        flash("Database offline.", "danger")
        return redirect(url_for('customer_dashboard'))
    cursor = db.cursor()
    
    try:
        # Update payment status
        cursor.execute("UPDATE service_requests SET payment_status = 'Paid' WHERE id = %s AND customer_id = %s", (request_id, session['user_id']))
        db.commit()
        flash("Payment successful! Thank you for using UrbanService.", "success")
    except Exception as e:
        flash(f"Payment failed: {e}", "danger")
    finally:
        return_db_connection(db)
        
    return redirect(url_for('customer_dashboard'))

@app.route('/worker/dashboard')
def worker_dashboard():
    if 'role' not in session or session['role'] != 'worker':
        return redirect(url_for('login'))
        
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('index'))
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Get worker details
    cursor.execute("""
        SELECT w.*, s.name as service_name 
        FROM workers w 
        JOIN services s ON w.service_id = s.id 
        WHERE w.id = %s
    """, (session['user_id'],))
    worker = cursor.fetchone()
    
    # Get active jobs
    cursor.execute("""
        SELECT sr.*, c.full_name as customer_name, c.phone as customer_phone, c.address, city.name as city_name, area.name as area_name, s.name as service_name
        FROM assignments a
        JOIN service_requests sr ON a.request_id = sr.id
        JOIN customers c ON sr.customer_id = c.id
        JOIN cities city ON sr.city_id = city.id
        JOIN areas area ON sr.area_id = area.id
        JOIN services s ON sr.service_id = s.id
        WHERE a.worker_id = %s AND (sr.status = 'Assigned' OR sr.status = 'On the way' OR sr.status = 'In Progress')
    """, (session['user_id'],))
    active_jobs = cursor.fetchall()
    
    # Get completed jobs
    cursor.execute("""
        SELECT sr.*, c.full_name as customer_name, c.phone as customer_phone, c.address, city.name as city_name, area.name as area_name, s.name as service_name, a.completed_at
        FROM assignments a
        JOIN service_requests sr ON a.request_id = sr.id
        JOIN customers c ON sr.customer_id = c.id
        JOIN cities city ON sr.city_id = city.id
        JOIN areas area ON sr.area_id = area.id
        JOIN services s ON sr.service_id = s.id
        WHERE a.worker_id = %s AND sr.status = 'Completed'
        ORDER BY a.completed_at DESC
    """, (session['user_id'],))
    completed_jobs = cursor.fetchall()
    
    # Get feedback for this worker
    cursor.execute("""
        SELECT fb.*, c.full_name as customer_name, s.name as service_name
        FROM feedback fb
        JOIN service_requests sr ON fb.request_id = sr.id
        JOIN customers c ON sr.customer_id = c.id
        JOIN services s ON sr.service_id = s.id
        JOIN assignments a ON a.request_id = sr.id
        WHERE a.worker_id = %s
        ORDER BY fb.created_at DESC
    """, (session['user_id'],))
    feedback_received = cursor.fetchall()
    
    return_db_connection(db)
    return render_template('worker_dashboard.html', worker=worker, jobs=active_jobs, completed_jobs=completed_jobs, feedback=feedback_received)

@app.route('/update_status', methods=['POST'])
def update_status():
    if 'role' not in session or session['role'] != 'worker':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    new_status = request.form['status']
    
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('worker_dashboard'))
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("UPDATE service_requests SET status = %s WHERE id = %s", (new_status, request_id))
        
        if new_status == 'On the way':
            # Set a mock ETA (25 minutes from now)
            from datetime import datetime, timedelta
            eta = datetime.now() + timedelta(minutes=25)
            cursor.execute("UPDATE assignments SET started_at = CURRENT_TIMESTAMP, eta = %s WHERE request_id = %s", (eta, request_id))
            flash("Journey started! Customer notified of your ETA.", "info")
            
        elif new_status == 'Completed':
            extra_charges = float(request.form.get('extra_charges', 0))
            
            # Fetch dynamic pricing from settings
            cursor.execute("SELECT value FROM system_settings WHERE key = 'platform_fee'")
            platform_convenience_fee = float(cursor.fetchone()['value'])
            cursor.execute("SELECT value FROM system_settings WHERE key = 'commission_pct'")
            comm_pct = float(cursor.fetchone()['value']) / 100.0
            
            # Fetch service fee
            cursor.execute("SELECT service_fee FROM service_requests WHERE id = %s", (request_id,))
            service_fee = float(cursor.fetchone()['service_fee'])
            
            total_amount = service_fee + extra_charges + platform_convenience_fee
            admin_commission = (service_fee * comm_pct) + platform_convenience_fee
            worker_share = total_amount - admin_commission
            
            cursor.execute("""
                UPDATE service_requests 
                SET status = 'Completed', 
                    extra_charges = %s, 
                    total_amount = %s, 
                    worker_share = %s, 
                    admin_commission = %s,
                    payment_status = 'Pending Approval'
                WHERE id = %s
            """, (extra_charges, total_amount, worker_share, admin_commission, request_id))
            
            cursor.execute("UPDATE assignments SET completed_at = CURRENT_TIMESTAMP WHERE request_id = %s", (request_id,))
            # Set worker back to available
            cursor.execute("UPDATE workers SET status = 'Available', jobs_completed = jobs_completed + 1 WHERE id = %s", (session['user_id'],))
            flash(f"Job completed! Total: ₹{total_amount}. Your share: ₹{worker_share}.", "success")
            
        db.commit()
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
        
    return redirect(url_for('worker_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('index'))
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    # Stats
    cursor.execute("SELECT COUNT(*) as total FROM service_requests")
    total_requests = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM workers")
    total_workers = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM service_requests WHERE status = 'Completed'")
    completed_jobs = cursor.fetchone()['total']
    
    # Calculate Total Admin Revenue
    cursor.execute("SELECT SUM(admin_commission) as total FROM service_requests WHERE status = 'Completed'")
    res = cursor.fetchone()
    total_revenue = float(res['total']) if res and res['total'] else 0.0
    
    # Pending Assignments
    cursor.execute("""
        SELECT sr.*, c.full_name as customer_name, s.name as service_name, city.name as city_name
        FROM service_requests sr
        JOIN customers c ON sr.customer_id = c.id
        JOIN services s ON sr.service_id = s.id
        JOIN cities city ON sr.city_id = city.id
        WHERE sr.status = 'Requested'
        ORDER BY sr.created_at ASC
    """,)
    pending_requests = cursor.fetchall()
    
    # All Workers - sorted by city
    cursor.execute("""
        SELECT w.*, s.name as service_name, city.name as city_name 
        FROM workers w 
        JOIN services s ON w.service_id = s.id
        JOIN cities city ON w.city_id = city.id
        ORDER BY city.name ASC, w.full_name ASC
    """)
    workers = cursor.fetchall()
    # Process workers to be JSON serializable
    processed_workers = []
    for w in workers:
        w_dict = dict(w)
        if w_dict.get('rating_avg'):
            w_dict['rating_avg'] = float(w_dict['rating_avg'])
        if w_dict.get('created_at'):
            w_dict['created_at'] = w_dict['created_at'].isoformat()
        processed_workers.append(w_dict)
    
    # All Cities and Services for modals
    cursor.execute("SELECT * FROM cities ORDER BY name ASC")
    cities = cursor.fetchall()
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    
    # All Feedback for monitoring
    cursor.execute("""
        SELECT fb.*, c.full_name as customer_name, s.name as service_name, w.full_name as worker_name
        FROM feedback fb
        JOIN service_requests sr ON fb.request_id = sr.id
        JOIN customers c ON sr.customer_id = c.id
        JOIN services s ON sr.service_id = s.id
        JOIN assignments a ON a.request_id = sr.id
        JOIN workers w ON a.worker_id = w.id
        ORDER BY fb.created_at DESC
    """)
    all_feedback = cursor.fetchall()
    
    # Complaints
    cursor.execute("""
        SELECT comp.*, c.full_name as customer_name, s.name as service_name, sr.request_date
        FROM complaints comp
        JOIN customers c ON comp.customer_id = c.id
        JOIN service_requests sr ON comp.request_id = sr.id
        JOIN services s ON sr.service_id = s.id
        ORDER BY comp.created_at DESC
    """)
    all_complaints = cursor.fetchall()

    # Get all completed requests for admin
    cursor.execute("""
        SELECT sr.*, c.full_name as customer_name, s.name as service_name, city.name as city_name, w.full_name as worker_name, a.completed_at
        FROM service_requests sr
        JOIN customers c ON sr.customer_id = c.id
        JOIN services s ON sr.service_id = s.id
        JOIN cities city ON sr.city_id = city.id
        JOIN assignments a ON sr.id = a.request_id
        JOIN workers w ON a.worker_id = w.id
        WHERE sr.status = 'Completed'
        ORDER BY a.completed_at DESC
    """)
    all_completed = cursor.fetchall()

    # Demand Heatmap Data (Requests by City)
    cursor.execute("""
        SELECT c.name as city_name, COUNT(sr.id) as request_count
        FROM cities c
        LEFT JOIN service_requests sr ON c.id = sr.city_id
        GROUP BY c.id, c.name
        ORDER BY request_count DESC
    """)
    heatmap_data = cursor.fetchall()

    # Financial Chart Data (Revenue by Category)
    cursor.execute("""
        SELECT s.name as service_name, SUM(sr.admin_commission) as revenue
        FROM services s
        JOIN service_requests sr ON s.id = sr.service_id
        WHERE sr.status = 'Completed'
        GROUP BY s.id, s.name
    """)
    chart_data = cursor.fetchall()

    # System Settings
    cursor.execute("SELECT * FROM system_settings")
    settings_list = cursor.fetchall()
    settings = {s['key']: s['value'] for s in settings_list}

    return_db_connection(db)
    return render_template('admin_dashboard.html', 
                          total_requests=total_requests, 
                          total_workers=total_workers, 
                          completed_jobs=completed_jobs,
                          pending_requests=pending_requests,
                          workers=processed_workers,
                          cities=cities,
                          services=services,
                          all_feedback=all_feedback,
                          all_complaints=all_complaints,
                          all_completed=all_completed,
                          total_revenue=total_revenue,
                          heatmap_data=heatmap_data,
                          chart_data=chart_data,
                          settings=settings)

@app.route('/admin/update_settings', methods=['POST'])
def update_settings():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    data = request.form
    db = get_db_connection()
    cursor = db.cursor()
    try:
        for key, value in data.items():
            cursor.execute("UPDATE system_settings SET value = %s WHERE key = %s", (value, key))
        db.commit()
        flash("System settings updated successfully.", "success")
    except Exception as e:
        flash(f"Error updating settings: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/verify_worker/<int:worker_id>', methods=['POST'])
def verify_worker(worker_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    status = request.form.get('status') == 'true'
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE workers SET is_verified = %s WHERE id = %s", (status, worker_id))
        db.commit()
        flash("Worker verification status updated.", "info")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/assign_worker', methods=['POST'])
def assign_worker():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    worker_id = request.form['worker_id']
    
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('admin_dashboard'))
    cursor = db.cursor()
    
    try:
        # Update request status
        cursor.execute("UPDATE service_requests SET status = 'Assigned' WHERE id = %s", (request_id,))
        # Add assignment
        cursor.execute("INSERT INTO assignments (request_id, worker_id) VALUES (%s, %s)", (request_id, worker_id))
        # Set worker to busy
        cursor.execute("UPDATE workers SET status = 'Busy' WHERE id = %s", (worker_id,))
        
        db.commit()
        flash("Worker assigned successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_city', methods=['POST'])
def add_city():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    name = request.form['name']
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('admin_dashboard'))
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO cities (name) VALUES (%s)", (name,))
        db.commit()
        flash("City added successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_service', methods=['POST'])
def add_service():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    name = request.form['name']
    desc = request.form['description']
    icon = request.form['icon']
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('admin_dashboard'))
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO services (name, description, icon_name) VALUES (%s, %s, %s)", (name, desc, icon))
        db.commit()
        flash("Service added successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    rating = int(request.form['rating'])
    comment = request.form['comment']
    
    db = get_db_connection()
    if not db:
        flash("Database connection offline.", "danger")
        return redirect(url_for('customer_dashboard'))
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Insert feedback
        cursor.execute("INSERT INTO feedback (request_id, rating, comment) VALUES (%s, %s, %s)", (request_id, rating, comment))
        
        # 2. Get worker ID for this request
        cursor.execute("SELECT worker_id FROM assignments WHERE request_id = %s", (request_id,))
        worker = cursor.fetchone()
        
        if worker:
            worker_id = worker['worker_id']
            # 3. Recalculate average rating
            cursor.execute("""
                SELECT AVG(f.rating) as new_avg 
                FROM feedback f
                JOIN assignments a ON f.request_id = a.request_id
                WHERE a.worker_id = %s
            """, (worker_id,))
            new_avg = cursor.fetchone()['new_avg']
            
            cursor.execute("UPDATE workers SET rating_avg = %s WHERE id = %s", (new_avg, worker_id))
            
        db.commit()
        flash("Thank you for your feedback!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
        
    return redirect(url_for('customer_dashboard'))

@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    if 'role' not in session or session['role'] != 'customer':
        return jsonify({'error': 'Unauthorized'}), 401
        
    worker_id = request.form['worker_id']
    customer_id = session['user_id']
    
    db = get_db_connection()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM customer_favorites WHERE customer_id = %s AND worker_id = %s", (customer_id, worker_id))
    fav = cursor.fetchone()
    
    if fav:
        cursor.execute("DELETE FROM customer_favorites WHERE customer_id = %s AND worker_id = %s", (customer_id, worker_id))
        status = 'removed'
    else:
        cursor.execute("INSERT INTO customer_favorites (customer_id, worker_id) VALUES (%s, %s)", (customer_id, worker_id))
        status = 'added'
        
    db.commit()
    return_db_connection(db)
    return jsonify({'status': status})

# --- New Feature Routes ---

@app.route('/cancel_request', methods=['POST'])
def cancel_request():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    reason = request.form['reason']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Update request status and reason
        cursor.execute("""
            UPDATE service_requests 
            SET status = 'Cancelled', cancellation_reason = %s, cancelled_at = CURRENT_TIMESTAMP 
            WHERE id = %s AND customer_id = %s
        """, (reason, request_id, session['user_id']))
        
        # Free up worker if assigned
        cursor.execute("SELECT worker_id FROM assignments WHERE request_id = %s", (request_id,))
        worker = cursor.fetchone()
        if worker:
            worker_id = worker[0]
            cursor.execute("UPDATE workers SET status = 'Available' WHERE id = %s", (worker_id,))
            
        db.commit()
        flash("Service cancelled successfully.", "info")
    except Exception as e:
        flash(f"Error cancelling: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('customer_dashboard'))

@app.route('/confirm_presence', methods=['POST'])
def confirm_presence():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    confirmation = request.form['confirmation'] # 'Yes' or 'Reschedule'
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        if confirmation == 'Yes':
            cursor.execute("UPDATE service_requests SET presence_confirmed = TRUE WHERE id = %s", (request_id,))
            flash("Availability confirmed! The worker will be dispatched shortly.", "success")
        else:
            # Reschedule logic could be complex, for now mark as needing reschedule or just cancel
            cursor.execute("UPDATE service_requests SET status = 'Cancelled', cancellation_reason = 'Customer requested reschedule' WHERE id = %s", (request_id,))
            flash("Request marked for rescheduling/cancellation.", "warning")
            
        db.commit()
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('customer_dashboard'))

@app.route('/worker/reject_task', methods=['POST'])
def reject_task():
    if 'role' not in session or session['role'] != 'worker':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    reason = request.form.get('reason', 'No reason provided')
    worker_id = session['user_id']
    
    db = get_db_connection()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Log rejection
        cursor.execute("INSERT INTO worker_rejections (request_id, worker_id, reason) VALUES (%s, %s, %s)", (request_id, worker_id, reason))
        
        # 2. Remove current assignment
        cursor.execute("DELETE FROM assignments WHERE request_id = %s AND worker_id = %s", (request_id, worker_id))
        
        # 3. Set worker to Available
        cursor.execute("UPDATE workers SET status = 'Available' WHERE id = %s", (worker_id,))
        
        # 4. Try to reassign
        cursor.execute("SELECT service_id, city_id FROM service_requests WHERE id = %s", (request_id,))
        req = cursor.fetchone()
        
        cursor.execute("""
            SELECT id FROM workers 
            WHERE service_id = %s AND city_id = %s AND status = 'Available' AND id != %s
            LIMIT 1
        """, (req['service_id'], req['city_id'], worker_id))
        
        new_worker = cursor.fetchone()
        if new_worker:
            new_worker_id = new_worker['id']
            cursor.execute("INSERT INTO assignments (request_id, worker_id) VALUES (%s, %s)", (request_id, new_worker_id))
            cursor.execute("UPDATE workers SET status = 'Busy' WHERE id = %s", (new_worker_id,))
            cursor.execute("UPDATE service_requests SET status = 'Assigned' WHERE id = %s", (request_id,))
            flash("Task rejected. We have automatically reassigned it to another worker.", "info")
        else:
            cursor.execute("UPDATE service_requests SET status = 'Requested' WHERE id = %s", (request_id,))
            flash("Task rejected. No other workers available right now. Admin will be notified.", "warning")
            
        db.commit()
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('worker_dashboard'))

@app.route('/raise_complaint', methods=['POST'])
def raise_complaint():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    request_id = request.form['request_id']
    category = request.form['category']
    description = request.form['description']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO complaints (request_id, customer_id, category, description)
            VALUES (%s, %s, %s, %s)
        """, (request_id, session['user_id'], category, description))
        db.commit()
        flash("Complaint raised successfully. We will look into it.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('customer_dashboard'))

@app.route('/repeat_booking', methods=['POST'])
def repeat_booking():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    old_request_id = request.form['request_id']
    
    db = get_db_connection()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM service_requests WHERE id = %s", (old_request_id,))
        old_req = cursor.fetchone()
        
        from datetime import datetime
        new_date = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO service_requests (customer_id, service_id, city_id, area_id, request_date, time_slot, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (session['user_id'], old_req['service_id'], old_req['city_id'], old_req['area_id'], new_date, old_req['time_slot'], old_req['description']))
        
        new_request_id = cursor.fetchone()['id']
        
        # Trigger auto-assignment for the new request
        cursor.execute("""
            SELECT id FROM workers 
            WHERE service_id = %s AND city_id = %s AND status = 'Available'
            LIMIT 1
        """, (old_req['service_id'], old_req['city_id']))
        
        worker = cursor.fetchone()
        if worker:
            cursor.execute("UPDATE service_requests SET status = 'Assigned' WHERE id = %s", (new_request_id,))
            cursor.execute("INSERT INTO assignments (request_id, worker_id) VALUES (%s, %s)", (new_request_id, worker['id']))
            cursor.execute("UPDATE workers SET status = 'Busy' WHERE id = %s", (worker['id'],))
            flash("Rebooked successfully! Smart Match found a worker.", "success")
        else:
            flash("Rebooked successfully! We are looking for available workers.", "info")
            
        db.commit()
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('customer_dashboard'))

@app.route('/admin/resolve_complaint', methods=['POST'])
def resolve_complaint():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    complaint_id = request.form['complaint_id']
    notes = request.form['notes']
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            UPDATE complaints 
            SET status = 'Resolved', resolution_notes = %s, resolved_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (notes, complaint_id))
        db.commit()
        flash("Complaint marked as resolved.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('admin_dashboard'))

@app.route('/customer/complaints')
def view_complaints():
    if 'role' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
        
    db = get_db_connection()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT c.*, s.name as service_name, sr.request_date
        FROM complaints c
        JOIN service_requests sr ON c.request_id = sr.id
        JOIN services s ON sr.service_id = s.id
        WHERE c.customer_id = %s
        ORDER BY c.created_at DESC
    """, (session['user_id'],))
    complaints = cursor.fetchall()
    return_db_connection(db)
    return render_template('complaints.html', complaints=complaints)

@app.route('/worker/toggle_status', methods=['POST'])
def toggle_worker_status():
    if 'role' not in session or session['role'] != 'worker':
        return redirect(url_for('login'))
        
    worker_id = session['user_id']
    
    db = get_db_connection()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT status FROM workers WHERE id = %s", (worker_id,))
        current_status = cursor.fetchone()['status']
        
        new_status = 'Offline' if current_status != 'Offline' else 'Available'
        cursor.execute("UPDATE workers SET status = %s WHERE id = %s", (new_status, worker_id))
        
        if new_status == 'Offline':
            # Unassign jobs that are only 'Assigned' (not 'In Progress' or 'On the way')
            cursor.execute("""
                SELECT request_id FROM assignments a
                JOIN service_requests sr ON a.request_id = sr.id
                WHERE a.worker_id = %s AND sr.status = 'Assigned'
            """, (worker_id,))
            stale_jobs = cursor.fetchall()
            
            for job in stale_jobs:
                cursor.execute("DELETE FROM assignments WHERE request_id = %s AND worker_id = %s", (job['request_id'], worker_id))
                cursor.execute("UPDATE service_requests SET status = 'Requested' WHERE id = %s", (job['request_id'],))
                
                # Try auto-reassign
                cursor.execute("SELECT service_id, city_id FROM service_requests WHERE id = %s", (job['request_id'],))
                req = cursor.fetchone()
                cursor.execute("""
                    SELECT id FROM workers 
                    WHERE service_id = %s AND city_id = %s AND status = 'Available' AND id != %s
                    LIMIT 1
                """, (req['service_id'], req['city_id'], worker_id))
                new_worker = cursor.fetchone()
                if new_worker:
                    cursor.execute("INSERT INTO assignments (request_id, worker_id) VALUES (%s, %s)", (job['request_id'], new_worker['id']))
                    cursor.execute("UPDATE workers SET status = 'Busy' WHERE id = %s", (new_worker['id'],))
                    cursor.execute("UPDATE service_requests SET status = 'Assigned' WHERE id = %s", (job['request_id'],))
            
            flash(f"Status changed to {new_status}. Pending tasks reassigned.", "info")
        else:
            flash(f"Status changed to {new_status}. You are now ready to receive jobs!", "success")
            
        db.commit()
    except Exception as e:
        flash(f"Error: {e}", "danger")
    finally:
        return_db_connection(db)
    return redirect(url_for('worker_dashboard'))

if __name__ == '__main__':
    # Disabling use_reloader to prevent [WinError 10038] on some Windows systems
    app.run(debug=True, port=5000, use_reloader=False)
