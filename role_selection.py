# Taxi Booking - Role Selection Screen
# This is the entry point. Users select their role (Admin/Driver/Customer) before logging in.
import customtkinter as ctk
from suppress_warnings import run_with_warning_suppression

# Configure theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


def open_role_selection():
    """Create and display the role selection window."""
    root = ctk.CTk()
    root.title("Taxi Booking - Select Role")
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

    # Title and subtitle
    title = ctk.CTkLabel(card, text="Select Your Role", text_color="#111111",
                         font=("Helvetica", 28, "bold"))
    title.pack(anchor="center", pady=(28, 2))
    subtitle = ctk.CTkLabel(card, text="Choose your role to continue.",
                            text_color="#7A7A7A", font=("Helvetica", 12))
    subtitle.pack(anchor="center", pady=(0, 28))

    # Role buttons container
    buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
    buttons_frame.pack(fill="both", expand=True, padx=18, pady=18)

    def open_admin_login():
        """Open login window for admin."""
        root.destroy()
        from admin_login import open_admin_login
        open_admin_login()

    def open_driver_login():
        """Open login window for driver."""
        root.destroy()
        from driver_login import open_driver_login
        open_driver_login()

    def open_customer_login():
        """Open login window for customer."""
        root.destroy()
        from login import create_login_window
        create_login_window("customer")

    # Admin Login Button
    admin_btn = ctk.CTkButton(
        buttons_frame,
        text="Admin Login",
        command=open_admin_login,
        height=50,
        corner_radius=16,
        fg_color="#111111",
        hover_color="#2A2A2A",
        text_color="white",
        font=("Helvetica", 14, "bold")
    )
    admin_btn.pack(fill="x", pady=(0, 12))

    # Driver Login Button
    driver_btn = ctk.CTkButton(
        buttons_frame,
        text="Driver Login",
        command=open_driver_login,
        height=50,
        corner_radius=16,
        fg_color="#111111",
        hover_color="#2A2A2A",
        text_color="white",
        font=("Helvetica", 14, "bold")
    )
    driver_btn.pack(fill="x", pady=(0, 12))

    # Customer Login Button
    customer_btn = ctk.CTkButton(
        buttons_frame,
        text="Customer Login",
        command=open_customer_login,
        height=50,
        corner_radius=16,
        fg_color="#111111",
        hover_color="#2A2A2A",
        text_color="white",
        font=("Helvetica", 14, "bold")
    )
    customer_btn.pack(fill="x", pady=(0, 12))

    # Footer text
    footer = ctk.CTkLabel(card, text="Don't have an account? Sign up in the login screen.",
                          text_color="#7A7A7A", font=("Helvetica", 10))
    footer.pack(anchor="center", pady=(12, 0))

    # Run mainloop with warning suppression
    run_with_warning_suppression(root)


# Entry point
if __name__ == "__main__":
    open_role_selection()
