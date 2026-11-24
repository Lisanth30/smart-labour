"""A small helper to exercise the database connection."""
from db_config import get_db_connection, return_db_connection

if __name__ == "__main__":
    conn = get_db_connection()
    if not conn:
        print("Unable to acquire a database connection.")
        exit(1)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())
    return_db_connection(conn)
    print("Connection returned successfully.")
