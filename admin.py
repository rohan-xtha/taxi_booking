import booking as booking_api
import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
from typing import List, Dict, Tuple
from db import get_conn


def list_all_bookings() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def assign_driver(booking_id: int, driver_id: int) -> Tuple[bool, str]:
    conn = get_conn()
    cur = conn.cursor()

    # verify driver
    cur.execute(
        "SELECT id FROM users WHERE id=? AND role='driver'", (driver_id,))
    if not cur.fetchone():
        conn.close()
        return False, "Driver not found."

    # target booking
    cur.execute("SELECT * FROM bookings WHERE id=?", (booking_id,))
    target = cur.fetchone()
    if not target:
        conn.close()
        return False, "Booking not found."
    if target["status"] in ("cancelled", "completed"):
        conn.close()
        return False, "Cannot assign driver to cancelled or completed booking."

    date = target["date"]
    time = target["time"]

    # Prevent assigning a driver if this customer already has an assigned/ booked
    # booking for the same pickup+dropoff location (avoid duplicate assignments)
    cust_id = target[1]  # customer_id
    pickup = target[2]   # pickup
    dropoff = target[3]  # dropoff
    cur.execute(
        """SELECT 1 FROM bookings WHERE customer_id=? AND pickup=? AND dropoff=?
                   AND status IN ('assigned','booked') AND id<>?""",
        (cust_id, pickup, dropoff, booking_id)
    )
    if cur.fetchone():
        conn.close()
        return False, "This customer already has an assigned/ booked ride for the same route."

    # overlap check (same date+time for that driver)
    cur.execute("""SELECT 1 FROM bookings
                   WHERE driver_id=? AND status IN ('assigned','booked')
                   AND date=? AND time=? AND id<>?""",
                (driver_id, date, time, booking_id))
    if cur.fetchone():
        conn.close()
        return False, "Driver has an overlapping booking at the same date and time."

    cur.execute("""UPDATE bookings SET driver_id=?, status='assigned' WHERE id=?""",
                (driver_id, booking_id))
    conn.commit()
    conn.close()
    return True, "Driver assigned."


# ---- Admin UI functions (moved from login.py) ----


def show_user_detail(parent, user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, name, address, phone, email FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        messagebox.showinfo('User', 'User not found.')
        return
    user = {'id': row[0], 'username': row[1], 'role': row[2], 'name': row[3], 'address': row[4] or '',
            'phone': row[5] or '', 'email': row[6] or ''}

    dlg = ctk.CTkToplevel(parent)
    dlg.title(f"User {user.get('id')}")
    dlg.geometry('420x260')
    dlg.grab_set()
    f = ctk.CTkFrame(dlg, fg_color='transparent')
    f.pack(fill='both', expand=True, padx=12, pady=12)
    ctk.CTkLabel(f, text=f"ID: {user.get('id')}", anchor='w').pack(fill='x')
    ctk.CTkLabel(
        f, text=f"Username: {user.get('username')}", anchor='w').pack(fill='x')
    ctk.CTkLabel(f, text=f"Role: {user.get('role')}",
                 anchor='w').pack(fill='x')
    ctk.CTkLabel(f, text=f"Name: {user.get('name')}",
                 anchor='w').pack(fill='x')
    ctk.CTkLabel(
        f, text=f"Address: {user.get('address')}", anchor='w').pack(fill='x')
    ctk.CTkLabel(
        f, text=f"Phone: {user.get('phone')}", anchor='w').pack(fill='x')
    ctk.CTkLabel(
        f, text=f"Email: {user.get('email')}", anchor='w').pack(fill='x')
    ctk.CTkButton(dlg, text='Close', command=dlg.destroy).pack(pady=8)


def admin_view_all_bookings(parent):
    rows = list_all_bookings()
    dlg = ctk.CTkToplevel(parent)
    dlg.title("All Bookings")
    dlg.geometry("820x420")
    dlg.grab_set()
    tree = ttk.Treeview(dlg, columns=("id", "customer_id", "pickup",
                        "dropoff", "date", "time", "status", "driver_id"), show="headings")
    cols = ("id", "customer_id", "pickup", "dropoff",
            "date", "time", "status", "driver_id")
    for c in cols:
        tree.heading(c, text=c.replace('_', ' ').capitalize())
        tree.column(c, width=100 if c in ("id", "customer_id",
                    "date", "time", "status") else 180, anchor='w')
    tree.pack(fill="both", expand=True, padx=8, pady=8)

    def load():
        for i in tree.get_children():
            tree.delete(i)
        for r in list_all_bookings():
            vals = (r['id'], r['customer_id'], r['pickup'], r['dropoff'],
                    r['date'], r['time'], r['status'], r.get('driver_id', ''))
            tree.insert("", "end", values=vals)

    def cancel_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(
                "No selection", "Please select a booking to cancel.")
            return
        vals = tree.item(sel[0], 'values')
        bid = int(vals[0])
        ok, msg = booking_api.cancel_booking(bid)
        if ok:
            messagebox.showinfo("Cancelled", msg)
            load()
        else:
            messagebox.showerror("Error", msg)

    btns = ctk.CTkFrame(dlg, fg_color='transparent')
    btns.pack(fill='x', padx=8, pady=(0, 8))
    ctk.CTkButton(btns, text='Refresh', command=load).pack(side='left', padx=6)
    ctk.CTkButton(btns, text='Cancel Booking', command=cancel_selected,
                  fg_color='#d9534f').pack(side='left', padx=6)

    def view_customer_from_selection():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo('No selection', 'Please select a booking.')
            return
        vals = tree.item(sel[0], 'values')
        cid = int(vals[1])
        show_user_detail(dlg, cid)

    def view_driver_from_selection():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo('No selection', 'Please select a booking.')
            return
        vals = tree.item(sel[0], 'values')
        did = vals[7] if len(vals) > 7 else None
        if not did:
            messagebox.showinfo(
                'No driver', 'No driver assigned for this booking.')
            return
        try:
            did_int = int(did)
        except Exception:
            messagebox.showinfo(
                'No driver', 'No driver assigned for this booking.')
            return
        show_user_detail(dlg, did_int)

    ctk.CTkButton(btns, text='View Customer',
                  command=view_customer_from_selection).pack(side='left', padx=6)
    ctk.CTkButton(btns, text='View Driver',
                  command=view_driver_from_selection).pack(side='left', padx=6)
    ctk.CTkButton(btns, text='Close', command=dlg.destroy).pack(
        side='right', padx=6)

    load()


def simple_input(parent, label):
    dlg = ctk.CTkToplevel(parent)
    dlg.title(label)
    v = tk.StringVar()
    ctk.CTkLabel(dlg, text=label).pack(padx=12, pady=(12, 4))
    e = ctk.CTkEntry(dlg, textvariable=v)
    e.pack(fill="x", padx=12, pady=4)
    e.focus_set()
    res = {"val": None}

    def ok():
        res["val"] = v.get().strip()
        dlg.destroy()
    ctk.CTkButton(dlg, text="OK", command=ok).pack(pady=8)
    dlg.grab_set()
    parent.wait_window(dlg)
    return res["val"]


def assign_driver_dialog(parent):
    bid = simple_input(parent, "Booking ID")
    did = simple_input(parent, "Driver ID")
    if not bid or not did:
        return
    try:
        ok, msg = assign_driver(int(bid), int(did))
        messagebox.showinfo("Assign Driver", msg)
    except ValueError:
        messagebox.showerror("Assign Driver", "IDs must be numbers.")


def show_customers(parent):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, username, address FROM users WHERE role='customer'")
    rows = cur.fetchall()
    conn.close()
    dlg = ctk.CTkToplevel(parent)
    dlg.title('Customers')
    dlg.geometry('640x360')
    dlg.grab_set()
    tree = ttk.Treeview(dlg, columns=(
        "id", "name", "username", "address"), show='headings')
    for c in ("id", "name", "username", "address"):
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=120 if c == 'id' else 180, anchor='w')
    tree.pack(fill='both', expand=True, padx=8, pady=8)
    for r in rows:
        vals = (r[0], r[1], r[2], r[3] or '')
        tree.insert('', 'end', values=vals)
    ctk.CTkButton(dlg, text='Close', command=dlg.destroy).pack(pady=8)


def show_all_drivers(parent):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, username, address FROM users WHERE role='driver'")
    rows = cur.fetchall()
    conn.close()

    dlg = ctk.CTkToplevel(parent)
    dlg.title('Drivers')
    dlg.geometry('700x420')
    dlg.grab_set()

    # Header
    header = ctk.CTkFrame(dlg, fg_color="#0E0E0E", height=56)
    header.pack(fill="x")
    header.pack_propagate(False)
    header_label = ctk.CTkLabel(header, text="Drivers", text_color="white",
                                font=("Helvetica", 16, "bold"))
    header_label.pack(pady=10)

    content = ctk.CTkFrame(dlg, fg_color="white")
    content.pack(fill="both", expand=True)

    inner = ctk.CTkFrame(content, fg_color="white")
    inner.pack(fill="both", expand=True, padx=16, pady=12)

    tree = ttk.Treeview(inner, columns=(
        "id", "name", "username", "address"), show='headings')
    for c in ("id", "name", "username", "address"):
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=120 if c == 'id' else 220, anchor='w')
    tree.pack(fill='both', expand=True)

    for r in rows:
        tree.insert('', 'end', values=(r[0], r[1], r[2], r[3] or ''))

    btn_frame = ctk.CTkFrame(inner, fg_color="white")
    btn_frame.pack(fill="x", pady=(12, 0))

    def refresh():
        for i in tree.get_children():
            tree.delete(i)
        conn2 = get_conn()
        cur2 = conn2.cursor()
        cur2.execute(
            "SELECT id, name, username, address FROM users WHERE role='driver'")
        for r in cur2.fetchall():
            tree.insert('', 'end', values=(r[0], r[1], r[2], r[3] or ''))
        conn2.close()

    ctk.CTkButton(btn_frame, text='🔄 Refresh', command=refresh,
                  fg_color="#2E4E47", hover_color="#1f6f65", text_color="white",
                  height=40, corner_radius=10).pack(side='left')
    ctk.CTkButton(btn_frame, text='Close', command=dlg.destroy,
                  fg_color="#d9534f", hover_color="#c9302c", text_color="white",
                  height=40, corner_radius=10).pack(side='right')


def open_admin_window(root, user):
    """Create the unified admin dashboard window.

    This function mirrors the previous admin dashboard layout that used to live
    inside `login.py`. It delegates actions to the helpers defined in this
    module (admin_view_all_bookings, assign_driver_dialog, show_customers,
    show_all_drivers).
    """
    if root:
        root.destroy()  # Close the previous (login) window

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
    win = ctk.CTk()
    win.title("Admin Dashboard")
    win.geometry("420x460")

    # Header with title
    header = ctk.CTkFrame(win, fg_color="#0E0E0E", corner_radius=0)
    header.pack(fill="x", pady=(0, 0))
    header_label = ctk.CTkLabel(header, text="Admin Dashboard", text_color="white",
                                font=("Helvetica", 24, "bold"))
    header_label.pack(pady=16)

    # Main content frame
    content = ctk.CTkFrame(win, fg_color="white", corner_radius=0)
    content.pack(fill="both", expand=True, padx=0, pady=0)

    # Button frame
    btn_frame = ctk.CTkFrame(content, fg_color="transparent")
    btn_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Styled buttons
    button_config = {
        "height": 50,
        "corner_radius": 12,
        "font": ("Helvetica", 14, "bold"),
        "text_color": "white"
    }

    ctk.CTkButton(btn_frame, text="📊 View All Bookings",
                  command=lambda: admin_view_all_bookings(win),
                  fg_color="#2E4E47", hover_color="#1f6f65", **button_config).pack(fill="x", pady=8)

    ctk.CTkButton(btn_frame, text="🚗 Assign Driver",
                  command=lambda: assign_driver_dialog(win),
                  fg_color="#2E4E47", hover_color="#1f6f65", **button_config).pack(fill="x", pady=8)

    ctk.CTkButton(btn_frame, text="👥 Customers",
                  command=lambda: show_customers(win),
                  fg_color="#2E4E47", hover_color="#1f6f65", **button_config).pack(fill="x", pady=8)

    ctk.CTkButton(btn_frame, text="🚕 Drivers",
                  command=lambda: show_all_drivers(win),
                  fg_color="#2E4E47", hover_color="#1f6f65", **button_config).pack(fill="x", pady=8)

    ctk.CTkButton(btn_frame, text="Close",
                  command=win.destroy, fg_color="#d9534f", hover_color="#c9302c",
                  **button_config).pack(fill="x", pady=8)

    win.mainloop()
