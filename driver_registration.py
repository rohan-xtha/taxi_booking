# Taxi Booking - Driver Registration Page
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from auth import register_customer, username_exists
from suppress_warnings import run_with_warning_suppression


def open_driver_registration(parent):
    """Create and display the driver registration window."""
    reg = ctk.CTkToplevel(parent)
    reg.title("Driver Registration")
    reg.geometry("360x750")
    reg.resizable(False, False)

    reg.transient(parent)
    reg.grab_set()

    # Top dark banner with logo placeholder
    banner = ctk.CTkFrame(reg, corner_radius=0, fg_color="#0E0E0E", height=180)
    banner.pack(fill="x")

    # Back arrow to return to login
    def go_back():
        reg.destroy()
        from driver_login import open_driver_login
        reg.after(0, open_driver_login)

    back_btn = ctk.CTkButton(banner, text="← Back", command=go_back, width=60, height=32,
                             corner_radius=8, fg_color="transparent", text_color="#7A7A7A",
                             hover_color="#e5e5e5", border_width=1, border_color="#d0d0d0")
    back_btn.place(x=12, y=12)

    logo_box = ctk.CTkFrame(banner, width=70, height=70,
                            corner_radius=18, fg_color="white")
    logo_box.place(relx=0.5, rely=0.55, anchor="center")
    logo_icon = ctk.CTkLabel(
        logo_box, text="▲", text_color="#0E0E0E", font=("Helvetica", 32, "bold"))
    logo_icon.place(relx=0.5, rely=0.5, anchor="center")

    # Rounded white card
    card = ctk.CTkFrame(reg, corner_radius=28, fg_color="white")
    card.pack(fill="both", expand=True, padx=16, pady=(12, 16))

    # Title and subtitle
    title = ctk.CTkLabel(card, text="Register as Driver",
                         text_color="#111111", font=("Helvetica", 24, "bold"))
    title.pack(anchor="center", pady=(24, 2))
    subtitle = ctk.CTkLabel(card, text="Fill in your details.",
                            text_color="#7A7A7A", font=("Helvetica", 12))
    subtitle.pack(anchor="center", pady=(0, 16))

    # Scrollable form
    form = ctk.CTkScrollableFrame(card, fg_color="transparent")
    form.pack(fill="both", expand=True, padx=18)

    fullname_var = tk.StringVar()
    address_var = tk.StringVar()
    phone_var = tk.StringVar()
    username_r_var = tk.StringVar()
    email_var = tk.StringVar()
    password_r_var = tk.StringVar()
    confirm_var = tk.StringVar()
    license_var = tk.StringVar()
    vehicle_var = tk.StringVar()

    def add_field(label, var, show=None, placeholder=""):
        """Helper function to add a labeled entry field."""
        ctk.CTkLabel(form, text=label, text_color="#7A7A7A", font=(
            "Helvetica", 10, "bold")).pack(anchor="w", pady=(10, 6))
        entry = ctk.CTkEntry(form, textvariable=var, show=show if show else None,
                             placeholder_text=placeholder, height=38, corner_radius=16)
        entry.pack(fill="x")
        return entry

    e_full = add_field("FULL NAME", fullname_var, placeholder="Your full name")
    e_addr = add_field("ADDRESS", address_var, placeholder="Your address")
    e_phone = add_field("PHONE", phone_var, placeholder="98XXXXXXXX")
    e_license = add_field("LICENSE NUMBER", license_var,
                          placeholder="Your driver license number")
    e_vehicle = add_field("VEHICLE", vehicle_var,
                          placeholder="Vehicle model/plate number")
    e_user = add_field("USERNAME", username_r_var,
                       placeholder="Choose a username")
    e_email = add_field("EMAIL", email_var, placeholder="name@example.com")
    e_pass = add_field("PASSWORD", password_r_var, show="*",
                       placeholder="Create a password")
    e_conf = add_field("CONFIRM PASSWORD", confirm_var,
                       show="*", placeholder="Retype password")

    def submit():
        """Handle driver registration."""
        full = fullname_var.get().strip()
        addr = address_var.get().strip()
        phone = phone_var.get().strip()
        license = license_var.get().strip()
        vehicle = vehicle_var.get().strip()
        user = username_r_var.get().strip()
        email = email_var.get().strip()
        pw = password_r_var.get()
        cpw = confirm_var.get()

        if not full or not addr or not phone or not license or not vehicle or not user or not email or not pw or not cpw:
            messagebox.showwarning("Missing information",
                                   "Please fill in all fields.")
            return
        if "@" not in email or "." not in email:
            messagebox.showwarning(
                "Invalid email", "Please enter a valid email address.")
            return
        if pw != cpw:
            messagebox.showwarning("Password mismatch",
                                   "Passwords do not match.")
            return
        if len(pw) < 6:
            messagebox.showwarning(
                "Weak password", "Password must be at least 6 characters.")
            return

        # Check if username already exists
        if username_exists(user):
            messagebox.showerror(
                "Username taken", "This username already exists. Please choose another.")
            return

        # Register as driver
        from db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""INSERT INTO users (username, password, role, name, address, phone, email)
                          VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (user, pw, "driver", full, addr, phone, email))
            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Registration Successful", f"Driver account created for {user}. You can now log in.")
            reg.destroy()
            # Return to login
            from driver_login import open_driver_login
            open_driver_login()
        except Exception as e:
            conn.close()
            messagebox.showerror("Registration failed",
                                 f"An error occurred: {str(e)}")

    # Footer with action buttons
    footer = ctk.CTkFrame(card, fg_color="white")
    footer.pack(side="bottom", fill="x")
    ctk.CTkButton(footer, text="Register", command=submit, height=40, corner_radius=10,
                  fg_color="#111111", hover_color="#2A2A2A", text_color="white").pack(fill="x", padx=18, pady=(12, 8))
    ctk.CTkButton(footer, text="Cancel", command=reg.destroy, height=36, corner_radius=10,
                  fg_color="#e5e5e5", hover_color="#d6d6d6", text_color="#111111").pack(fill="x", padx=18, pady=(0, 12))

    e_full.focus_set()


# Entry point
if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Standalone Driver Registration")
    ctk.CTkButton(root, text="Open Driver Registration",
                  command=lambda: open_driver_registration(root)).pack(padx=20, pady=20)
    run_with_warning_suppression(root)
