import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk

import booking as booking_api


def view_my_bookings(parent, user):
    # Open an interactive bookings window for the customer with cancel capability
    dlg = ctk.CTkToplevel(parent)
    dlg.title("My Bookings")
    dlg.geometry("760x360")
    tree = ttk.Treeview(dlg, columns=("id", "date", "time", "pickup",
                                            "dropoff", "status", "driver_id"), show="headings")
    cols = ("id", "date", "time", "pickup", "dropoff", "status", "driver_id")
    for c in cols:
        tree.heading(c, text=c.replace('_', ' ').capitalize())
        tree.column(c, width=100 if c in (
            "id", "date", "time", "status") else 180, anchor='w')
    tree.pack(fill="both", expand=True, padx=8, pady=8)

    def load():
        for i in tree.get_children():
            tree.delete(i)
        rows = booking_api.list_bookings_by_customer(user["id"])
        for r in rows:
            tree.insert("", "end", values=(
                r['id'], r['date'], r['time'], r['pickup'], r['dropoff'], r['status'], r.get('driver_id')))

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
            messagebox.showinfo('Cancelled', msg)
            load()
        else:
            messagebox.showerror('Error', msg)

    btns = ctk.CTkFrame(dlg, fg_color='transparent')
    btns.pack(fill='x', padx=8, pady=(0, 8))
    ctk.CTkButton(btns, text='Refresh', command=load).pack(side='left', padx=6)
    ctk.CTkButton(btns, text='Cancel Booking', command=cancel_selected,
                  fg_color='#d9534f').pack(side='left', padx=6)
    ctk.CTkButton(btns, text='Close', command=dlg.destroy).pack(
        side='right', padx=6)

    load()


def show_available_drivers(parent):
    """Show drivers who are not currently assigned/booked using themed layout.

    This window matches the dark-header / white-content / green-button theme
    used across other dashboards.
    """
    from db import get_conn
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, name, username, address FROM users WHERE role='driver' AND id NOT IN (
            SELECT driver_id FROM bookings WHERE driver_id IS NOT NULL AND status IN ('assigned','booked')
        )"""
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        messagebox.showinfo("Available Drivers",
                            "No available drivers right now.")
        return

    dlg = ctk.CTkToplevel(parent)
    dlg.title("Available Drivers")
    dlg.geometry("640x380")
    dlg.grab_set()

    # Dark header
    header = ctk.CTkFrame(dlg, fg_color="#0E0E0E", height=56)
    header.pack(fill="x")
    header.pack_propagate(False)
    header_label = ctk.CTkLabel(header, text="Available Drivers", text_color="white",
                                font=("Helvetica", 16, "bold"))
    header_label.pack(pady=10)

    # White content area
    content = ctk.CTkFrame(dlg, fg_color="white")
    content.pack(fill="both", expand=True)

    inner = ctk.CTkFrame(content, fg_color="white")
    inner.pack(fill="both", expand=True, padx=16, pady=12)

    tree = ttk.Treeview(inner, columns=(
        "id", "name", "username", "address"), show="headings")
    for c in ("id", "name", "username", "address"):
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=120 if c == 'id' else 220, anchor='w')
    # Add scrollbars
    vsb = ttk.Scrollbar(inner, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(inner, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")

    for r in rows:
        try:
            vals = (r[0], r[1], r[2], r[3] or "")
        except Exception:
            vals = (r['id'], r.get('name'), r.get(
                'username'), r.get('address'))
        tree.insert('', 'end', values=vals)

    btn_frame = ctk.CTkFrame(inner, fg_color="white")
    btn_frame.pack(fill="x", pady=(12, 0))

    def refresh():
        for i in tree.get_children():
            tree.delete(i)
        # reload rows
        conn2 = get_conn()
        cur2 = conn2.cursor()
        cur2.execute(
            """SELECT id, name, username, address FROM users WHERE role='driver' AND id NOT IN (
                SELECT driver_id FROM bookings WHERE driver_id IS NOT NULL AND status IN ('assigned','booked')
            )"""
        )
        for r in cur2.fetchall():
            tree.insert('', 'end', values=(r[0], r[1], r[2], r[3] or ""))
        conn2.close()

    refresh_btn = ctk.CTkButton(btn_frame, text="🔄 Refresh", command=refresh,
                                fg_color="#2E4E47", hover_color="#1f6f65", text_color="white",
                                height=40, corner_radius=10)
    refresh_btn.pack(side='left')

    close_btn = ctk.CTkButton(btn_frame, text="Close", command=dlg.destroy,
                              fg_color="#d9534f", hover_color="#c9302c", text_color="white",
                              height=40, corner_radius=10)
    close_btn.pack(side='right')
