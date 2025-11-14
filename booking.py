from typing import List, Dict, Optional, Tuple
from db import get_conn


def create_booking(customer_id: int, pickup: str, dropoff: str, date: str, time: str) -> Tuple[bool, str, Optional[Dict]]:
    if not all([customer_id, pickup, dropoff, date, time]):
        return False, "All fields are required.", None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO bookings (customer_id, pickup, dropoff, date, time, status, driver_id)
                   VALUES (?, ?, ?, ?, ?, 'booked', NULL)""",
                (customer_id, pickup.strip(), dropoff.strip(), date.strip(), time.strip()))
    booking_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    row = cur.fetchone()
    conn.close()
    return True, f"Booking created with ID {booking_id}.", dict(row) if row else None


def list_bookings_by_customer(customer_id: int) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE customer_id=?", (customer_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def update_booking(booking_id: int,
                   pickup: Optional[str] = None,
                   dropoff: Optional[str] = None,
                   date: Optional[str] = None,
                   time: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Booking not found.", None
    if row["status"] in ("cancelled", "completed"):
        conn.close()
        return False, "Cannot update a cancelled or completed booking.", None

    new_pickup = pickup.strip() if pickup is not None else row["pickup"]
    new_dropoff = dropoff.strip() if dropoff is not None else row["dropoff"]
    new_date = date.strip() if date is not None else row["date"]
    new_time = time.strip() if time is not None else row["time"]

    cur.execute("""UPDATE bookings
                   SET pickup=?, dropoff=?, date=?, time=?
                   WHERE id=?""",
                (new_pickup, new_dropoff, new_date, new_time, booking_id))
    conn.commit()
    cur.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    updated = dict(cur.fetchone())
    conn.close()
    return True, "Booking updated.", updated


def cancel_booking(booking_id: int) -> Tuple[bool, str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status FROM bookings WHERE id=?", (booking_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Booking not found."
    if row["status"] == "cancelled":
        conn.close()
        return False, "Booking already cancelled."
    cur.execute(
        "UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    return True, "Booking cancelled."


def auto_assign_driver(booking_id: int) -> Tuple[bool, str, Optional[int]]:
    """Try to automatically assign an available driver to the booking.

    Strategy (simple): pick the first driver who does not already have a booking
    at the same date+time with status 'assigned' or 'booked'. Returns (ok,msg,driver_id).
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT date, time FROM bookings WHERE id=?", (booking_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Booking not found.", None
    date = row["date"]
    time = row["time"]

    # Find drivers who are not busy at the given date/time
    cur.execute(
        """SELECT id FROM users WHERE role='driver' AND id NOT IN (
                SELECT driver_id FROM bookings
                WHERE date=? AND time=? AND driver_id IS NOT NULL
                AND status IN ('assigned','booked')
            )
        """,
        (date, time)
    )
    candidates = [r["id"] for r in cur.fetchall()]
    if not candidates:
        conn.close()
        return False, "No available drivers at that time.", None

    # Choose the first candidate (simple policy). Could be improved to nearest/least-busy.
    chosen = candidates[0]
    cur.execute(
        "UPDATE bookings SET driver_id=?, status='assigned' WHERE id=?", (chosen, booking_id))
    conn.commit()
    conn.close()
    return True, f"Driver {chosen} assigned.", chosen


def complete_booking(booking_id: int) -> Tuple[bool, str]:
    """Mark a booking as completed."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status FROM bookings WHERE id=?", (booking_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Booking not found."
    if row["status"] == "completed":
        conn.close()
        return False, "Booking already completed."
    cur.execute(
        "UPDATE bookings SET status='completed' WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()
    return True, "Booking marked as completed."
