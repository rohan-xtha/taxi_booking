# Taxi Booking - Admin Login Page
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from suppress_warnings import run_with_warning_suppression


def open_admin_login():
    """Create and display the admin login window."""
    # Configure theme
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    root.title("Taxi Booking - Admin Login")
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
    title = ctk.CTkLabel(card, text="Admin Login", text_color="#111111",
                         font=("Helvetica", 28, "bold"))
    title.pack(anchor="center", pady=(28, 2))
    subtitle = ctk.CTkLabel(card, text="Sign in as admin.",
                            text_color="#7A7A7A", font=("Helvetica", 12))
    subtitle.pack(anchor="center", pady=(0, 18))

    # Fields
    form = ctk.CTkFrame(card, fg_color="transparent")
    form.pack(fill="x", padx=18)

    # Admin ID
    admin_id_var = tk.StringVar()
    id_label = ctk.CTkLabel(
        form, text="ADMIN ID", text_color="#7A7A7A", font=("Helvetica", 10, "bold"))
    id_label.pack(anchor="w", pady=(0, 6))
    admin_id_entry = ctk.CTkEntry(form, textvariable=admin_id_var,
                                  placeholder_text="Your admin ID", height=38, corner_radius=16)
    admin_id_entry.pack(fill="x")

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

    def do_admin_login():
        """Validate admin credentials against the users DB and open the unified admin window."""
        admin_id = admin_id_var.get().strip()
        password = password_var.get()

        # Check fields are not empty
        if not admin_id or not password:
            show_alert("Please enter both admin ID and password.",
                       kind="warning")
            return

        # Authenticate against DB using auth.login to avoid hardcoded credentials
        try:
            from auth import login as auth_login
            ok, role_or_msg, user = auth_login(admin_id, password)
        except Exception:
            ok, role_or_msg, user = False, "Auth error", None

        if not ok:
            show_alert("Invalid admin ID or password.", kind="error")
            return

        # Ensure role is admin
        if role_or_msg != 'admin':
            show_alert("User is not an admin.", kind="error")
            return

        # Success: open the unified admin window implemented in login.py
        show_alert("Login successful!", kind="success", timeout=800)
        try:
            # import inside function to avoid circular import at module load
            from login import open_admin_window as open_admin_from_login
            # close this login root and open the main admin window
            # Don't pass root since it will be destroyed
            root.after(800, lambda: (root.destroy(),
                       open_admin_from_login(None, user)))
        except Exception as e:
            # fallback: open local simple dashboard
            show_alert(f"Error opening admin window: {str(e)}", kind="error")
            root.after(800, lambda: root.destroy())

    def on_enter_key(event):
        do_admin_login()

    # Inline alert label
    alert_label = ctk.CTkLabel(card, text="", font=(
        "Helvetica", 10, "bold"), text_color="#d9534f")
    alert_label.pack(fill="x", padx=18, pady=(6, 6))

    login_button = ctk.CTkButton(card, text="Log in", command=do_admin_login, height=40,
                                 corner_radius=10, fg_color="#111111", hover_color="#2A2A2A", text_color="white")
    login_button.pack(fill="x", padx=18, pady=(6, 12))

    # Keyboard: press Enter to login
    root.bind("<Return>", on_enter_key)

    # Focus
    admin_id_entry.focus_set()

    run_with_warning_suppression(root)


def open_admin_window(root):
    """Open the admin dashboard window."""
    win = ctk.CTkToplevel(root)
    win.title("Admin Dashboard")
    win.geometry("400x300")
    win.grab_set()

    # Header
    header = ctk.CTkLabel(win, text="Admin Dashboard", text_color="#111111",
                          font=("Helvetica", 20, "bold"))
    header.pack(pady=(20, 10))

    # Admin options
    button_frame = ctk.CTkFrame(win, fg_color="transparent")
    button_frame.pack(fill="both", expand=True, padx=20, pady=10)

    view_bookings_btn = ctk.CTkButton(
        button_frame, text="View All Bookings", height=40,
        corner_radius=10, fg_color="#111111", hover_color="#2A2A2A", text_color="white"
    )
    view_bookings_btn.pack(fill="x", pady=(0, 10))

    assign_driver_btn = ctk.CTkButton(
        button_frame, text="Assign Driver", height=40,
        corner_radius=10, fg_color="#111111", hover_color="#2A2A2A", text_color="white"
    )
    assign_driver_btn.pack(fill="x", pady=(0, 10))

    logout_btn = ctk.CTkButton(
        button_frame, text="Logout", height=40,
        corner_radius=10, fg_color="transparent", text_color="#7A7A7A",
        border_width=1, border_color="#d0d0d0", hover_color="#e5e5e5",
        command=lambda: (win.destroy(), root.destroy())
    )
    logout_btn.pack(fill="x", pady=(0, 10))


# Entry point
if __name__ == "__main__":
    open_admin_login()
