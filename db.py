import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "taxi_booking.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('customer','driver','admin')),
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT
    )""")

    # bookings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        pickup TEXT NOT NULL,
        dropoff TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('booked','assigned','cancelled','completed')),
        driver_id INTEGER,
        FOREIGN KEY (customer_id) REFERENCES users(id),
        FOREIGN KEY (driver_id) REFERENCES users(id)
    )""")

    # helpful indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bookings_customer ON bookings(customer_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bookings_driver ON bookings(driver_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bookings_date_time ON bookings(date,time)")

    conn.commit()
    conn.close()