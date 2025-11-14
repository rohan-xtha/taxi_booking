# Taxi Booking - Driver Login Page
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk
from auth import login as auth_login
from suppress_warnings import run_with_warning_suppression
import booking as booking_api
import driver as driver_api


def open_driver_login():
    """Create and display the driver login window."""
    # Configure theme
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    root.title("Taxi Booking - Driver Login")
    root.geometry("360x640")
    root.resizable(False, False)

    # Top dark banner with logo placeholder
    banner = ctk.CTkFrame(root, corner_radius=0,
                          fg_color="#0E0E0E", height=200)
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

    # Back button (top-left of card) - closes login and returns to role selection
    def go_back():
        root.destroy()
        from role_selection import open_role_selection
        root.after(0, open_role_selection)

    back_btn = ctk.CTkButton(
        card, text="← Back", command=go_back, width=60, height=32,
        corner_radius=8, fg_color="transparent", text_color="#7A7A7A",
        hover_color="#e5e5e5", border_width=1, border_color="#d0d0d0"
    )
    back_btn.place(x=12, y=12)

    # Title and subtitle
    title = ctk.CTkLabel(card, text="Driver Login", text_color="#111111",
                         font=("Helvetica", 28, "bold"))
    title.pack(anchor="center", pady=(28, 2))
    subtitle = ctk.CTkLabel(card, text="Sign in to your account.",
                            text_color="#7A7A7A", font=("Helvetica", 12))
    subtitle.pack(anchor="center", pady=(0, 18))

    # Fields
    form = ctk.CTkFrame(card, fg_color="transparent")
    form.pack(fill="x", padx=18)

    # Username
    username_var = tk.StringVar()
    username_label = ctk.CTkLabel(
        form, text="USERNAME", text_color="#7A7A7A", font=("Helvetica", 10, "bold"))
    username_label.pack(anchor="w", pady=(0, 6))
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

    # Login button + handlers
    alert_timer = None

    def show_alert(msg: str, kind: str = "error", timeout: int = 4000):
        """Display an inline alert above the login button."""
        nonlocal alert_timer
        colors = {"error": "#d9534f",
                  "warning": "#f0ad4e", "success": "#5cb85c"}
        clr = colors.get(kind, "#d9534f")
        alert_label.configure(text=msg, text_color=clr)
        try:
            if alert_timer:
                root.after_cancel(alert_timer)
        except Exception:
            pass
        alert_timer = None
        if timeout and msg:
            alert_timer = root.after(
                timeout, lambda: alert_label.configure(text=""))

    def do_driver_login():
        """Validate driver credentials and open driver dashboard."""
        username = username_var.get().strip()
        password = password_var.get()

        # Check fields are not empty
        if not username or not password:
            show_alert("Please enter both username and password.",
                       kind="warning")
            return

        # Authenticate using the auth system
        ok, role, user = auth_login(username, password)
        if ok and role == "driver":
            show_alert("Login successful!", kind="success", timeout=1500)
            # Open driver window after brief delay
            root.after(1500, lambda: open_driver_window(root, user))
        elif ok:
            show_alert("This account is not a driver account.", kind="error")
        else:
            show_alert("Invalid username or password.", kind="error")

    def on_enter_key(event):
        do_driver_login()

    # Inline alert label
    alert_label = ctk.CTkLabel(card, text="", font=(
        "Helvetica", 10, "bold"), text_color="#d9534f")
    alert_label.pack(fill="x", padx=18, pady=(6, 6))

    login_button = ctk.CTkButton(card, text="Log in", command=do_driver_login, height=40,
                                 corner_radius=10, fg_color="#111111", hover_color="#2A2A2A", text_color="white")
    login_button.pack(fill="x", padx=18, pady=(6, 12))

    # Secondary actions (Sign up)
    links = ctk.CTkFrame(card, fg_color="transparent")
    links.pack(fill="x", padx=18, pady=(0, 12))

    signup_frame = ctk.CTkFrame(links, fg_color="transparent")
    signup_frame.pack(side="right", anchor="e")
    signup_btn = ctk.CTkButton(signup_frame, text="Register as Driver", command=lambda: open_driver_registration_window(root),
                               fg_color="transparent", text_color="#0078D4", hover=False)
    signup_btn.pack(side="right")

    # Keyboard: press Enter to login
    root.bind("<Return>", on_enter_key)

    # Focus
    username_entry.focus_set()

    run_with_warning_suppression(root)


def open_driver_registration_window(parent):
    """Open driver registration window from login."""
    from driver_registration import open_driver_registration
    open_driver_registration(parent)


def open_driver_window(root, user):
    """Open the driver dashboard window and list bookings assigned to this driver."""
    win = ctk.CTkToplevel(root)
    win.title("Driver Dashboard")
    win.geometry("700x420")
    win.grab_set()

    # Header
    header = ctk.CTkLabel(win, text=f"Welcome, {user.get('name', 'Driver')}!", text_color="#111111",
                          font=("Helvetica", 20, "bold"))
    header.pack(pady=(12, 6))

    # Bookings list
    frame = ctk.CTkFrame(win, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=12, pady=6)

    cols = ("id", "customer_id", "pickup", "dropoff", "date", "time", "status")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c.replace("_", " ").capitalize())
        tree.column(c, width=100 if c in ("id", "customer_id",
                    "date", "time", "status") else 180, anchor="w")
    # Add scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")

    btn_frame = ctk.CTkFrame(win, fg_color="transparent")
    btn_frame.pack(fill="x", padx=12, pady=(6, 12))

    def load_bookings():
        for i in tree.get_children():
            tree.delete(i)
        rows = driver_api.list_bookings_by_driver(user["id"])
        for r in rows:
            tree.insert("", "end", values=(
                r["id"], r["customer_id"], r["pickup"], r["dropoff"], r["date"], r["time"], r["status"]))

    def view_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a booking.")
            return
        vals = tree.item(sel[0], "values")
        text = "\n".join([f"{k}: {v}" for k, v in zip(cols, vals)])
        messagebox.showinfo("Booking details", text)

    def mark_complete():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(
                "No selection", "Please select a booking to mark complete.")
            return
        vals = tree.item(sel[0], "values")
        bid = int(vals[0])
        ok, msg = booking_api.complete_booking(bid)
        if ok:
            messagebox.showinfo("Success", msg)
            load_bookings()
        else:
            messagebox.showerror("Error", msg)

    refresh_btn = ctk.CTkButton(
        btn_frame, text="Refresh", command=load_bookings)
    refresh_btn.pack(side="left", padx=(0, 8))
    view_btn = ctk.CTkButton(btn_frame, text="View", command=view_selected)
    view_btn.pack(side="left", padx=(0, 8))
    complete_btn = ctk.CTkButton(btn_frame, text="Mark Completed",
                                 command=mark_complete, fg_color="#2E4E47", text_color="white")
    complete_btn.pack(side="right")

    load_bookings()


# Entry point
if __name__ == "__main__":
    open_driver_login()
