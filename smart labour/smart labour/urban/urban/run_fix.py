import psycopg2
from db_config import get_db_connection, return_db_connection

def fix_assignments():
    print("Applying fix for assignments table...")
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        with open('fix_assignments_schema.sql', 'r') as f:
            sql = f.read()
            cursor.execute(sql)
        conn.commit()
        print("Assignments table updated successfully!")
    except Exception as e:
        print(f"Error updating assignments: {e}")
        conn.rollback()
    finally:
        cursor.close()
        return_db_connection(conn)

if __name__ == "__main__":
    fix_assignments()
