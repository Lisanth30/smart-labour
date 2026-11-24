import psycopg2
from db_config import get_db_connection, return_db_connection

def migrate():
    db = get_db_connection()
    if not db:
        print("Failed to connect to database.")
        return
    
    cursor = db.cursor()
    
    try:
        print("Applying schema updates...")
        
        # 1. Update workers table
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS bio TEXT DEFAULT 'Professional service provider.';")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS rating_avg DECIMAL(3,2) DEFAULT 5.0;")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS jobs_completed INT DEFAULT 0;")
        cursor.execute("ALTER TABLE workers ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;")
        
        # 2. Update service_requests status check constraint
        try:
            cursor.execute("ALTER TABLE service_requests DROP CONSTRAINT IF EXISTS service_requests_status_check;")
            cursor.execute("""
                ALTER TABLE service_requests 
                ADD CONSTRAINT service_requests_status_check 
                CHECK (status IN ('Requested', 'Assigned', 'On the way', 'In Progress', 'Completed', 'Cancelled'));
            """)
        except Exception as e:
            print(f"Note: Status check update handled: {e}")

        # 3. Update assignments table for ETA tracking
        cursor.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS eta TIMESTAMP;")
        cursor.execute("ALTER TABLE assignments ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;")

        # 4. Create customer_favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_favorites (
                id SERIAL PRIMARY KEY,
                customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
                worker_id INT REFERENCES workers(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(customer_id, worker_id)
            );
        """)

        # 5. Create system_settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key VARCHAR(100) PRIMARY KEY,
                value VARCHAR(255)
            );
        """)
        cursor.execute("""
            INSERT INTO system_settings (key, value) VALUES 
            ('platform_fee', '49.0'), 
            ('commission_pct', '15.0') 
            ON CONFLICT (key) DO NOTHING;
        """)

        # 6. Create complaints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id SERIAL PRIMARY KEY,
                request_id INT REFERENCES service_requests(id) ON DELETE CASCADE,
                customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
                category VARCHAR(100),
                description TEXT,
                status VARCHAR(50) DEFAULT 'Open',
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            );
        """)

        # 7. Create worker_rejections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS worker_rejections (
                id SERIAL PRIMARY KEY,
                request_id INT REFERENCES service_requests(id) ON DELETE CASCADE,
                worker_id INT REFERENCES workers(id) ON DELETE CASCADE,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        db.commit()
        print("Migration successful!")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.close()
        return_db_connection(db)

if __name__ == "__main__":
    migrate()
