import psycopg2
from db_config import get_db_connection, return_db_connection

def fix_constraint():
    print("Updating status check constraint...")
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database.")
        return

    try:
        cursor = conn.cursor()
        with open('fix_status_constraint.sql', 'r') as f:
            sql = f.read()
            cursor.execute(sql)
        conn.commit()
        print("Constraint updated successfully!")
    except Exception as e:
        print(f"Error updating constraint: {e}")
        conn.rollback()
    finally:
        cursor.close()
        return_db_connection(conn)

if __name__ == "__main__":
    fix_constraint()
