import os
import traceback
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as psycopg2_pool
from psycopg2.extras import RealDictCursor

# Read configuration from environment with sane defaults
DB_SETTINGS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Connection pool holder
_connection_pool = None


def _ensure_database_exists():
    temp_conn = None
    cur = None
    try:
        temp_conn = psycopg2.connect(
            host=DB_SETTINGS["host"],
            user=DB_SETTINGS["user"],
            password=DB_SETTINGS["password"],
            port=DB_SETTINGS["port"],
        )
        temp_conn.autocommit = True
        cur = temp_conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_SETTINGS["database"],),
        )
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {DB_SETTINGS['database']}")
            print(f"[OK] Database '{DB_SETTINGS['database']}' created")
        else:
            print(f"[OK] Database '{DB_SETTINGS['database']}' already exists")
        return True
    except psycopg2.Error as exc:
        print(f"[ERROR] Error ensuring database exists: {exc}")
        traceback.print_exc()
        return False
    finally:
        if cur:
            cur.close()
        if temp_conn:
            temp_conn.close()


def _initialize_connection_pool(pool_name="urban_pool", pool_size=None):
    global _connection_pool
    if pool_size is None:
        try:
            pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        except ValueError:
            pool_size = 10
    try:
        _connection_pool = psycopg2_pool.SimpleConnectionPool(
            minconn=1,
            maxconn=pool_size,
            host=DB_SETTINGS["host"],
            port=DB_SETTINGS["port"],
            database=DB_SETTINGS["database"],
            user=DB_SETTINGS["user"],
            password=DB_SETTINGS["password"],
        )
        print(f"[OK] PostgreSQL connection pool '{pool_name}' created (size={pool_size})")
        return True
    except psycopg2.Error as exc:
        print(f"[ERROR] Error creating connection pool: {exc}")
        traceback.print_exc()
        _connection_pool = None
        return False


def get_db_connection():
    global _connection_pool
    if not _connection_pool:
        if not _initialize_connection_pool():
            return None
    try:
        return _connection_pool.getconn()
    except psycopg2.Error as exc:
        print(f"[ERROR] Error getting DB connection: {exc}")
        traceback.print_exc()
        return None


def return_db_connection(conn):
    # For psycopg2 pooled connections, putconn() returns connection to pool
    try:
        if conn and _connection_pool:
            _connection_pool.putconn(conn)
    except Exception:
        pass


@contextmanager
def db_cursor(dictionary=True):
    conn = get_db_connection()
    if not conn:
        raise psycopg2.Error("Failed to acquire DB connection")
    cur = None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor) if dictionary else conn.cursor()
        yield cur
        try:
            conn.commit()
        except psycopg2.Error as exc:
            print(f"[ERROR] Commit error: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
    except psycopg2.Error as exc:
        print(f"[ERROR] DB query error: {exc}")
        traceback.print_exc()
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        if cur:
            cur.close()
        return_db_connection(conn)


def _apply_sql_file(conn, filepath):
    if not os.path.exists(filepath):
        print(f"[ERROR] SQL file not found: {filepath}")
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            sql_content = f.read()
        cur = conn.cursor()
        cur.execute(sql_content)
        conn.commit()
        cur.close()
        print(f"[OK] Applied {os.path.basename(filepath)}")
        return True
    except Exception as exc:
        print(f"[ERROR] Error applying SQL file: {exc}")
        traceback.print_exc()
        return False


def init_db():
    global _connection_pool
    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION (PostgreSQL)")
    print("=" * 60)
    if not _ensure_database_exists():
        print("[ERROR] Failed to ensure database exists")
        return False
    _connection_pool = None
    if not _initialize_connection_pool():
        print("[ERROR] Failed to initialize connection pool")
        return False
    print("\nApplying schema...")
    conn = None
    try:
        conn = psycopg2.connect(**DB_SETTINGS)
        schema_path = os.path.join(SCRIPT_DIR, "schema.sql")
        if not _apply_sql_file(conn, schema_path):
            print("[ERROR] Failed to apply main schema")
            return False
        
        print("\n[OK] Database initialization completed")
        return True
    except psycopg2.Error as exc:
        print(f"[ERROR] Error during DB initialization: {exc}")
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("PostgreSQL Database Configuration")
    print(f"Host: {DB_SETTINGS['host']}")
    print(f"Port: {DB_SETTINGS['port']}")
    print(f"Database: {DB_SETTINGS['database']}")
    print(f"User: {DB_SETTINGS['user']}\n")
    if init_db():
        print("\nTesting DB connection...")
        conn = get_db_connection()
        if conn:
            print("[OK] DB connection test successful")
            return_db_connection(conn)
        else:
            print("[ERROR] Failed to get DB connection")