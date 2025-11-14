# Taxi Booking - Login with Role Windows (SQLite-backed)
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from db import init_db
from auth import seed_defaults, login as auth_login
from registration import open_registration

import booking as booking_api
import admin as admin_api
import driver as driver_api
from booking_ui import open_booking_window, open_menu_window

# Initialize DB and defaults
init_db()
seed_defaults()

# ---------- Configuration ----------
BG_MAIN = "#3C8071"
BG_HEADER = "#519B8B"
BG_FRAME = "#62968f"
BG_LABEL1 = "#4a746e"
BG_LABEL2 = "#44635f"
BG_BTN = "#2E4E47"
BG_BTN_SECONDARY = "#1f6f65"
FG_TEXT = "white"

# ---------- Shared Handlers ----------


def toggle_password():
    if password_entry.cget("show") == "":
        password_entry.config(show="*")
        show_hide_btn.config(text="Show")
    else:
        password_entry.config(show="")
        show_hide_btn.config(text="Hide")


def on_enter_key(event):
    do_login()


def view_my_bookings(parent, user):
    rows = booking_api.list_bookings_by_customer(user["id"])
    if not rows:
        messagebox.showinfo("My Bookings", "No bookings.")
        return
    text = "\n".join([f"ID {b['id']} | {b['date']} {b['time']} {b['pickup']} -> {b['dropoff']} | "
                      f"{b['status']} | driver={b.get('driver_id')}" for b in rows])
    show_text(parent, "My Bookings", text)
# Admin window should use CustomTkinter for consistency


def open_admin_window(root, user):
    win = ctk.CTkToplevel(root)
    win.title("Admin")
    win.geometry("300x200")  # Added a default size
    win.grab_set()  # Make it modal
    ctk.CTkButton(win, text="View All Bookings",
                  command=lambda: view_all_bookings(win)).pack(fill="x", expand=True, padx=12, pady=6)
    ctk.CTkButton(win, text="Assign Driver",
                  command=lambda: assign_driver_dialog(win)).pack(fill="x", expand=True, padx=12, pady=6)
    ctk.CTkButton(win, text="Close", command=win.destroy, fg_color="transparent",
                  border_width=1, border_color="gray").pack(fill="x", expand=True, padx=12, pady=12)


def view_all_bookings(parent):
    rows = admin_api.list_all_bookings()
    if not rows:
        messagebox.showinfo("All Bookings", "No bookings.")
        return
    text = "\n".join([f"ID {b['id']} | cust={b['customer_id']} | {b['date']} {b['time']} "
                      f"{b['pickup']} -> {b['dropoff']} | {b['status']} | driver={b.get('driver_id')}"
                      for b in rows])
    show_text(parent, "All Bookings", text)


def assign_driver_dialog(parent):
    bid = simple_input(parent, "Booking ID")
    did = simple_input(parent, "Driver ID")
    if not bid or not did:
        return
    try:
        ok, msg = admin_api.assign_driver(int(bid), int(did))
        messagebox.showinfo("Assign Driver", msg)
    except ValueError:
        messagebox.showerror("Assign Driver", "IDs must be numbers.")

# Driver window should use CustomTkinter for consistency


def open_driver_window(root, user):
    win = ctk.CTkToplevel(root)
    win.title("Driver")
    win.geometry("300x150")  # Added a default size
    win.grab_set()  # Make it modal
    ctk.CTkButton(win, text="View My Trips",
                  command=lambda: view_driver_trips(win, user)).pack(fill="x", expand=True, padx=12, pady=6)
    ctk.CTkButton(win, text="Close", command=win.destroy, fg_color="transparent",
                  border_width=1, border_color="gray").pack(fill="x", expand=True, padx=12, pady=12)


def view_driver_trips(parent, user):
    rows = driver_api.list_bookings_by_driver(user["id"])
    if not rows:
        messagebox.showinfo("My Trips", "No assigned trips.")
        return
    text = "\n".join([f"ID {b['id']} | {b['date']} {b['time']} {b['pickup']} -> {b['dropoff']} "
                      f"| {b['status']}" for b in rows])
    show_text(parent, "My Trips", text)

# Helper for simple text input dialogs


def simple_input(parent, label):
    dlg = ctk.CTkToplevel(parent)  # Use CTkToplevel
    dlg.title(label)
    v = tk.StringVar()
    # Use CTkLabel and CTkEntry for consistency
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
# Helper for displaying text in a dialog


def show_text(parent, title, text):
    dlg = ctk.CTkToplevel(parent)  # Use CTkToplevel
    dlg.title(title)
    # Use CTkTextbox if available, otherwise tk.Text is fine for now
    # For simple display, a CTkLabel with wrapping might also work
    t = ctk.CTkTextbox(dlg, width=450, height=250)
    t.pack(fill="both", expand=True, padx=12, pady=12)
    t.insert("1.0", text)
    t.configure(state="disabled")
    ctk.CTkButton(dlg, text="Close", command=dlg.destroy).pack(pady=(0, 12))


# Taxi Booking - Login with Registration + Role Windows (SQLite)
# ---------- UI Setup ----------
# Use CustomTkinter for a modern look matching the mock
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

root = ctk.CTk()
root.title("Taxi Booking Login")
root.geometry("360x640")
root.resizable(False, False)

# Top dark banner with logo placeholder
banner = ctk.CTkFrame(root, corner_radius=0, fg_color="#0E0E0E", height=200)
banner.pack(fill="x")
logo_box = ctk.CTkFrame(banner, width=76, height=76,
                        corner_radius=18, fg_color="white")
logo_box.place(relx=0.5, rely=0.52, anchor="center")
logo_icon = ctk.CTkLabel(
    logo_box, text="▲", text_color="#0E0E0E", font=("Helvetica", 36, "bold"))
logo_icon.place(relx=0.5, rely=0.5, anchor="center")

# Rounded white card
card = ctk.CTkFrame(root, corner_radius=28, fg_color="white")
card.pack(fill="both", expand=True, padx=16, pady=(12, 16))

# Title and subtitle
title = ctk.CTkLabel(card, text="Login", text_color="#111111",
                     font=("Helvetica", 28, "bold"))
title.pack(anchor="center", pady=(28, 2))
subtitle = ctk.CTkLabel(card, text="Sign in to continue.",
                        text_color="#7A7A7A", font=("Helvetica", 12))
subtitle.pack(anchor="center", pady=(0, 18))

# Fields
form = ctk.CTkFrame(card, fg_color="transparent")
form.pack(fill="x", padx=18)

# Username
username_var = tk.StringVar()
name_label = ctk.CTkLabel(
    form, text="NAME", text_color="#7A7A7A", font=("Helvetica", 10, "bold"))
name_label.pack(anchor="w", pady=(0, 6))
username_entry = ctk.CTkEntry(form, textvariable=username_var,
                              placeholder_text="Your username", height=38, corner_radius=16)
username_entry.pack(fill="x")

# Password
password_var = tk.StringVar()
password_label = ctk.CTkLabel(
    form, text="PASSWORD", text_color="#7A7A7A", font=("Helvetica", 10, "bold"))
password_label.pack(anchor="w", pady=(14, 6))
password_entry = ctk.CTkEntry(form, textvariable=password_var, show="*",
                              placeholder_text="Your password", height=38, corner_radius=16)
password_entry.pack(fill="x")

# Login button
# Inline alert label (shows warnings/errors above the login button)
alert_timer = None


def show_alert(msg: str, kind: str = "error", timeout: int = 4000):
    """Display an inline alert above the login button.

    kind: "error" (red), "warning" (orange), "success" (green)
    timeout: milliseconds to auto-clear (0 = don't auto-clear)
    """
    global alert_timer
    colors = {"error": "#d9534f", "warning": "#f0ad4e", "success": "#5cb85c"}
    clr = colors.get(kind, "#d9534f")
    alert_label.configure(text=msg, text_color=clr)
    # cancel previous timer
    try:
        if alert_timer:
            root.after_cancel(alert_timer)
    except Exception:
        pass
    alert_timer = None
    if timeout and msg:
        alert_timer = root.after(
            timeout, lambda: alert_label.configure(text=""))


alert_label = ctk.CTkLabel(card, text="", font=(
    "Helvetica", 10, "bold"), text_color="#d9534f")
alert_label.pack(fill="x", padx=18, pady=(6, 6))

login_button = ctk.CTkButton(card, text="Log in", command=do_login, height=40,
                             corner_radius=10, fg_color="#111111", hover_color="#2A2A2A", text_color="white")
login_button.pack(fill="x", padx=18, pady=(6, 12))

# Secondary actions (Forgot + Sign up)
links = ctk.CTkFrame(card, fg_color="transparent")
links.pack(fill="x")

# Left: forgot password
forgot_frame = ctk.CTkFrame(links, fg_color="transparent")
forgot_frame.pack(side="left", anchor="w")
forgot_btn = ctk.CTkButton(forgot_frame, text="Forgot Password?", command=lambda: messagebox.showinfo(
    "Forgot Password", "Please contact admin."), fg_color="transparent", text_color="#7A7A7A", hover=False)
forgot_btn.pack(pady=(4, 0), side="left")

# Right: sign up (more visible)
signup_frame = ctk.CTkFrame(links, fg_color="transparent")
signup_frame.pack(side="right", anchor="e")
signup_btn = ctk.CTkButton(signup_frame, text="Sign up", command=lambda: open_registration(
    root), fg_color="transparent", text_color="#0078D4", hover=False)
signup_btn.pack(pady=(0, 12), side="right")

# Keyboard: press Enter to login
root.bind("<Return>", on_enter_key)

# Focus
username_entry.focus_set()

root.mainloop()
