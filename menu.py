import customtkinter as ctk
from tkinter import messagebox


def open_side_menu(parent, user):
    """Create and show a left side menu anchored to `parent`.

    parent: the container (frame) where the side menu will be placed (e.g. the `top` frame in booking_ui)
    user: dict-like object with at least 'name' or 'username' """

    existing = getattr(parent, "_side_menu", None)
    if existing and str(existing) in map(str, parent.winfo_children()):
        return

    side = ctk.CTkFrame(parent, width=280, fg_color="#0e0e0e")
    side.place(x=0, y=0, relheight=1)

    def close_side():
        try:
            side.destroy()
        except Exception:
            pass
        try:
            delattr(parent, "_side_menu")
        except Exception:
            setattr(parent, "_side_menu", None)

    close_btn = ctk.CTkButton(side, text="X", width=36, height=36, corner_radius=18,
                              fg_color="#2a2a2a", hover_color="#3a3a3a", text_color="white",
                              command=close_side)
    close_btn.place(x=232, y=12)

    # Profile area
    prof_box = ctk.CTkFrame(side, width=64, height=64,
                            corner_radius=32, fg_color="#2a2a2a")
    prof_box.place(x=18, y=20)
    prof_lbl = ctk.CTkLabel(prof_box, text="\u25CF",
                            text_color="#bfbfbf", font=("Helvetica", 28))
    prof_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # Username (from logged-in user)
    name = user.get("name") if isinstance(
        user, dict) else getattr(user, "name", None)
    if not name:
        name = user.get("username") if isinstance(
            user, dict) else getattr(user, "username", "User")

    name_label = ctk.CTkLabel(side, text=name, font=(
        "Helvetica", 18, "bold"), text_color="white")
    name_label.place(x=100, y=30)

    # Divider
    sep = ctk.CTkFrame(side, height=1, fg_color="#2a2a2a")
    sep.place(x=0, y=110, relwidth=1)

    # Menu buttons (placeholder callbacks)
    # Replaced 'City' with 'Driver' so users can quickly view available drivers
    items = ["Driver", "Request history", "Couriers", "City to City", "Freight", "Notifications",
             "Safety", "Settings", "Help", "Support"]
    y = 126
    # helper to show available drivers. Try customer view first, fallback to admin list.

    def _show_available_drivers():
        try:
            from customer import show_available_drivers as _cust_show
            _cust_show(parent)
            return
        except Exception:
            try:
                from admin import show_all_drivers as _admin_show
                _admin_show(parent)
                return
            except Exception:
                messagebox.showinfo("Drivers", "No driver view available.")

    for it in items:
        if it == "Driver":
            cmd = _show_available_drivers
        else:
            def cmd(t=it): return messagebox.showinfo(t, f"{t} clicked")
        b = ctk.CTkButton(side, text=it, fg_color="transparent", hover_color="#1a1a1a", text_color="#ffffff",
                          anchor="w", height=38, corner_radius=8, command=cmd)
        b.place(x=18, y=y, relwidth=0.85)
        y += 44

    # Driver mode large button at bottom
    def driver_mode():
        messagebox.showinfo(
            "Driver mode", "Switching to driver mode (not implemented)")

    driver_btn = ctk.CTkButton(side, text="Driver mode", fg_color="#d6ff2a", text_color="#111111",
                               height=44, corner_radius=12, command=driver_mode)
    driver_btn.place(x=18, y=520, relwidth=0.86)

    # Store reference on parent so it can be checked/closed by other code if needed
    setattr(parent, "_side_menu", side)


if __name__ == "__main__":
    # Quick manual test harness (only runs when executing menu.py directly)
    import tkinter as tk
    root = tk.Tk()
    root.geometry("360x640")
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
    top = ctk.CTkFrame(root)
    top.pack(fill="both", expand=True)
    open_side_menu(top, {"name": "Rohan shrestha"})
    root.mainloop()
