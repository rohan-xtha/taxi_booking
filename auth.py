from typing import Optional, Tuple, Dict
from db import get_conn, init_db

def seed_defaults():
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    # admin
    cur.execute("SELECT 1 FROM users WHERE username=?", ("admin",))
    if not cur.fetchone():
        cur.execute("""INSERT INTO users (username,password,role,name,address,phone,email)
                       VALUES (?,?,?,?,?,?,?)""",
                    ("admin","admin123","admin","Administrator","", "", "admin@example.com"))
    # driver1
    cur.execute("SELECT 1 FROM users WHERE username=?", ("driver1",))
    if not cur.fetchone():
        cur.execute("""INSERT INTO users (username,password,role,name,address,phone,email)
                       VALUES (?,?,?,?,?,?,?)""",
                    ("driver1","driver123","driver","Driver One","", "9800000000", "driver1@example.com"))
    conn.commit()
    conn.close()

def username_exists(username: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username=?", (username,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def register_customer(name: str, address: str, phone: str, email: str,
                      username: str, password: str) -> Tuple[bool, str]:
    if not all([name, address, phone, email, username, password]):
        return False, "All fields are required."
    if username_exists(username):
        return False, "Username already exists."
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO users (username,password,role,name,address,phone,email)
                   VALUES (?,?,?,?,?,?,?)""",
                (username, password, "customer", name, address, phone, email))
    conn.commit()
    conn.close()
    return True, f"Customer registered: {username}"

def login(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT id, username, password, role, name, address, phone, email
                   FROM users WHERE username=? AND password=?""", (username, password))
    row = cur.fetchone()
    conn.close()
    if row:
        user = dict(row)
        return True, user["role"], user
    return False, "Invalid username or password.", None