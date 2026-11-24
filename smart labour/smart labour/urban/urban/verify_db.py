import psycopg2
from db_config import get_db_connection, return_db_connection

def verify_setup():
    print("--- Verification Report ---")
    
    # Check 1: Connection
    db = get_db_connection()
    if not db:
        print("FAILED: Could not connect to the database. Check your credentials in db_config.py.")
        return
    else:
        print("SUCCESS: Database connection established.")

    cursor = db.cursor()

    # Check 2: Tables existence
    expected_tables = [
        'admins', 'cities', 'areas', 'services', 'customers', 'workers', 
        'service_requests', 'assignments', 'feedback', 'customer_favorites',
        'system_settings', 'complaints', 'worker_rejections'
    ]
    found_tables = []
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        rows = cursor.fetchall()
        found_tables = [row[0] for row in rows]
        
        missing_tables = [t for t in expected_tables if t not in found_tables]
        
        if not missing_tables:
            print(f"SUCCESS: All {len(expected_tables)} tables exist.")
        else:
            print(f"WARNING: Missing tables: {', '.join(missing_tables)}")
            print("Action: Run 'python db_config.py' to create them.")

        # Check 3: Admin User Seeded
        if 'admins' in found_tables:
            cursor.execute("SELECT COUNT(*) FROM admins")
            admin_count = cursor.fetchone()[0]
            if admin_count > 0:
                print(f"SUCCESS: {admin_count} Admin(s) found in the database.")
            else:
                print("FAILED: No Admin users found.")
                print("Action: Run 'python seed.py' to seed the data.")

        # Check 4: Other Seed Data
        if 'cities' in found_tables and 'services' in found_tables:
            cursor.execute("SELECT COUNT(*) FROM cities")
            city_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM services")
            service_count = cursor.fetchone()[0]
            print(f"INFO: Found {city_count} cities and {service_count} services.")

    except Exception as e:
        print(f"ERROR while verifying: {e}")
    finally:
        cursor.close()
        return_db_connection(db)

if __name__ == "__main__":
    verify_setup()
