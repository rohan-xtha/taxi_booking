# Taxi Booking - Login with Role Windows (SQLite-backed)
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk

from db import init_db
from auth import seed_defaults, login as auth_login
from registration import open_registration

 

# role UIs moved to separate modules
from admin import open_admin_window
from driver import open_driver_window

# Initialize DB and defaults
init_db()
seed_defaults()


# Taxi Booking - Login with Registration + Role Windows (SQLite)
# ---------- Main Login Window Function ----------

def _create_banner(parent: ctk.CTk) -> ctk.CTkFrame:
    """Creates the top banner with a logo placeholder."""
    # Top dark banner with logo placeholder
    banner = ctk.CTkFrame(parent, corner_radius=0,
                          fg_color="#0E0E0E", height=200)
    banner.pack(fill="x")
    logo_box = ctk.CTkFrame(banner, width=76, height=76,
                            corner_radius=18, fg_color="white")
    logo_box.place(relx=0.5, rely=0.52, anchor="center")
    logo_icon = ctk.CTkLabel(
        logo_box, text="▲", text_color="#0E0E0E", font=("Helvetica", 36, "bold"))
    logo_icon.place(relx=0.5, rely=0.5, anchor="center")
    return banner


def _create_login_card(root: ctk.CTk, selected_role: str) -> ctk.CTkFrame:
    """Creates the main login card with form fields and buttons."""
    # Rounded white card
    card = ctk.CTkFrame(root, corner_radius=28, fg_color="white")
    card.pack(fill="both", expand=True, padx=16, pady=(12, 16))

    # Back button (top-left of card) - closes login and returns to role selection
    def go_back():
        from role_selection import open_role_selection
        root.destroy()
        open_role_selection()

    back_btn = ctk.CTkButton(
        card, text="← Back", command=go_back, width=60, height=32,
        corner_radius=8, fg_color="transparent", text_color="#7A7A7A",
        hover_color="#e5e5e5", border_width=1, border_color="#d0d0d0"
    )
    back_btn.place(x=12, y=12)

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

    # Login button + handlers (must be defined before use)
    alert_timer = None

    def show_alert(msg: str, kind: str = "error", timeout: int = 4000):
        """Display an inline alert above the login button."""
        nonlocal alert_timer
        colors = {"error": "#d9534f",
                  "warning": "#f0ad4e", "success": "#5cb85c"}
        clr = colors.get(kind, "#d9534f")
        try:
            if not alert_label.winfo_exists(): return
            alert_label.configure(text=msg, text_color=clr)
            if alert_timer:
                root.after_cancel(alert_timer)
        except Exception:
            pass
        if timeout and msg:
            alert_timer = root.after(
                timeout, lambda: alert_label.configure(text=""))

    def do_login():
        username = username_var.get().strip()
        password = password_var.get()
        if not username or not password:
            show_alert("Please enter both username and password.",
                       kind="warning")
            return
        ok, role, user = auth_login(username, password)
        if ok:
            if role == "customer":
                try:
                    from booking_ui import open_menu_window
                except Exception:
                    show_alert("Customer menu is unavailable.", kind="error")
                    return
                root.withdraw()
                open_menu_window(root, user)
            elif role == "admin": # The root window is withdrawn/destroyed inside open_admin_window
                open_admin_window(root, user)
            elif role == "driver":
                open_driver_window(root, user)
        else:
            show_alert(role or "Login failed", kind="error")

    def on_enter_key(event):
        do_login()

    # Inline alert label
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

    return card


def create_login_window(selected_role="all"):
    """Create and display the login window with optional role-specific title."""
    # Use CustomTkinter for a modern look matching the mock
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    root.title(f"Taxi Booking - {selected_role.capitalize()} Login" if selected_role != "all" else "Taxi Booking Login")
    root.geometry("360x640")
    root.resizable(False, False)

    _create_banner(root)
    _create_login_card(root, selected_role)

    root.mainloop()


# ---------- Entry Point ----------
if __name__ == "__main__":
    create_login_window("all")
