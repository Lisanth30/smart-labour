import psycopg2
from db_config import get_db_connection, return_db_connection

def run_migration():
    print("Running database migration to sync schema...")
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        with open('update_schema.sql', 'r') as f:
            sql = f.read()
            # Split by SQL statement delimiter (e.g., semicolon) if needed, 
            # but psycopg2 often handles multi-statement strings.
            cursor.execute(sql)
        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        cursor.close()
        return_db_connection(conn)

if __name__ == "__main__":
    run_migration()
