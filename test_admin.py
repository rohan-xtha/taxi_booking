from auth import seed_defaults, login
from db import get_conn

# Initialize database with defaults
seed_defaults()

# Check if admin exists
conn = get_conn()
cur = conn.cursor()
cur.execute(
    'SELECT id, username, password, role, name FROM users WHERE role="admin"')
admin_row = cur.fetchone()
print("Admin user in DB:", admin_row)
conn.close()

# Test login
print("\nTesting admin login with username='admin', password='admin123':")
ok, role, user = login("admin", "admin123")
print(f"Login result: ok={ok}, role={role}")
if user:
    print(
        f"User data: id={user['id']}, username={user['username']}, role={user['role']}, name={user['name']}")
