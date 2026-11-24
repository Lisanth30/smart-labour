import psycopg2
from db_config import get_db_connection, return_db_connection

def apply_indexes():
    print("Applying database indexes...")
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        with open('add_indexes.sql', 'r') as f:
            sql = f.read()
            cursor.execute(sql)
        conn.commit()
        print("Indexes applied successfully!")
    except Exception as e:
        print(f"Error applying indexes: {e}")
        conn.rollback()
    finally:
        cursor.close()
        return_db_connection(conn)

if __name__ == "__main__":
    apply_indexes()
