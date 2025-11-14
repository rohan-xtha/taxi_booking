import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from auth import register_customer


BG_MAIN = "#3C8071"
BG_FRAME = "#62968f"
BG_LABEL1 = "#4a746e"
BG_LABEL2 = "#44635f"
BG_BTN = "#2E4E47"
BG_BTN_SECONDARY = "#1f6f65"
FG_TEXT = "white"

def open_registration(root):
    reg = ctk.CTkToplevel(root)
    reg.title("Create Account")
    reg.geometry("360x700")
    reg.resizable(False, False)

    reg.transient(root)
    reg.grab_set()

    # Top dark banner with logo placeholder
    banner = ctk.CTkFrame(reg, corner_radius=0, fg_color="#0E0E0E", height=180)
    banner.pack(fill="x")

    # Back arrow to return to login
    back_btn = ctk.CTkButton(banner, text="\u2190", width=36, height=36, corner_radius=18,
                              fg_color="#1f1f1f", hover_color="#2a2a2a", text_color="white",
                              command=reg.destroy)
    back_btn.place(x=12, y=12)

    logo_box = ctk.CTkFrame(banner, width=70, height=70, corner_radius=18, fg_color="white")
    logo_box.place(relx=0.5, rely=0.55, anchor="center")
    logo_icon = ctk.CTkLabel(logo_box, text="▲", text_color="#0E0E0E", font=("Helvetica", 32, "bold"))
    logo_icon.place(relx=0.5, rely=0.5, anchor="center")

    # Rounded white card
    card = ctk.CTkFrame(reg, corner_radius=28, fg_color="white")
    card.pack(fill="both", expand=True, padx=16, pady=(12, 16))

    # Title and subtitle
    title = ctk.CTkLabel(card, text="Create Account", text_color="#111111", font=("Helvetica", 24, "bold"))
    title.pack(anchor="center", pady=(24, 2))
    subtitle = ctk.CTkLabel(card, text="Fill in the details below.", text_color="#7A7A7A", font=("Helvetica", 12))
    subtitle.pack(anchor="center", pady=(0, 16))

    # Scrollable form so buttons remain visible on smaller screens
    form = ctk.CTkScrollableFrame(card, fg_color="transparent")
    form.pack(fill="both", expand=True, padx=18)

    fullname_var = tk.StringVar()
    address_var = tk.StringVar()
    phone_var = tk.StringVar()
    username_r_var = tk.StringVar()
    email_var = tk.StringVar()
    password_r_var = tk.StringVar()
    confirm_var = tk.StringVar()

    def add_field(label, var, show=None, placeholder=""):
        ctk.CTkLabel(form, text=label, text_color="#7A7A7A", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(10, 6))
        entry = ctk.CTkEntry(form, textvariable=var, show=show if show else None,
                             placeholder_text=placeholder, height=38, corner_radius=16)
        entry.pack(fill="x")
        return entry

    e_full = add_field("FULL NAME", fullname_var, placeholder="Your full name")
    e_addr = add_field("ADDRESS", address_var, placeholder="Your address")
    e_phone = add_field("PHONE", phone_var, placeholder="98XXXXXXXX")
    e_user = add_field("USERNAME", username_r_var, placeholder="Choose a username")
    e_email = add_field("EMAIL", email_var, placeholder="name@example.com")
    e_pass = add_field("PASSWORD", password_r_var, show="*", placeholder="Create a password")
    e_conf = add_field("CONFIRM PASSWORD", confirm_var, show="*", placeholder="Retype password")

    def submit():
        full = fullname_var.get().strip()
        addr = address_var.get().strip()
        phone = phone_var.get().strip()
        user = username_r_var.get().strip()
        email = email_var.get().strip()
        pw = password_r_var.get()
        cpw = confirm_var.get()

        if not full or not addr or not phone or not user or not email or not pw or not cpw:
            messagebox.showwarning("Missing information", "Please fill in all fields.")
            return
        if "@" not in email or "." not in email:
            messagebox.showwarning("Invalid email", "Please enter a valid email address.")
            return
        if pw != cpw:
            messagebox.showwarning("Password mismatch", "Passwords do not match.")
            return

        ok, msg = register_customer(full, addr, phone, email, user, pw)
        if ok:
            messagebox.showinfo("Registered", msg)
            reg.destroy()
        else:
            messagebox.showerror("Registration failed", msg)

    # Footer with action buttons pinned at bottom
    footer = ctk.CTkFrame(card, fg_color="white")
    footer.pack(side="bottom", fill="x")
    ctk.CTkButton(footer, text="Register", command=submit, height=40, corner_radius=10,
                  fg_color="#111111", hover_color="#2A2A2A", text_color="white").pack(fill="x", padx=18, pady=(12, 8))
    ctk.CTkButton(footer, text="Cancel", command=reg.destroy, height=36, corner_radius=10,
                  fg_color="#e5e5e5", hover_color="#d6d6d6", text_color="#111111").pack(fill="x", padx=18, pady=(0, 12))

    e_full.focus_set()


if __name__ == "__main__":
    root = ctk.CTk()
    root.title("Standalone Registration")
    ctk.CTkButton(root, text="Open Registration", command=lambda: open_registration(root)).pack(padx=20, pady=20)
    tk.Button(root, text="Open Registration", command=lambda: open_registration(root)).pack(padx=20, pady=20)
    root.mainloop()