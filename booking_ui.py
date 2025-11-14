import tkinter as tk
from tkinter import messagebox, ttk
import random
from datetime import datetime
from typing import Optional

import customtkinter as ctk

# pip install tkintermapview
from tkintermapview import TkinterMapView
import menu
import math
import booking as booking_api
from db import get_conn
from map import geocode, get_route_coords, nominatim_search, haversine, enable_location
from driver import _load_drivers, show_nearby_drivers, start_driver_coord_preloader

# CustomTkinter theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

BG_MAIN = "#3C8071"
BG_FRAME = "#62968f"
BG_BTN = "#2E4E47"
BG_BTN_SECONDARY = "#1f6f65"
FG_TEXT = "white"

# Popular places used for quick suggestions under the search box.
# Edit this list to change suggestions shown in the UI.
POPULAR_PLACES = [
    "Thamel",
    "Patan Durbar Square",
    "Swayambhunath (Monkey Temple)",
    "Pashupatinath Temple",
    "Boudhanath Stupa",
    "Tribhuvan International Airport (KTM)",
    "New Road",
    "Lazimpat",
    "Bhatbhateni Supermarket",
    "Durbar Marg"
]

# Performance / tuning constants
ANIMATION_STEPS = 8      # fewer frames -> faster animations

# The route modal was removed in favor of inline route controls rendered
# directly in the map overlay below. The functions that draw and fetch
# routes are implemented later in the map UI (open_menu_window).


def open_booking_window(root, user, prefill_pickup: str = "", prefill_drop: str = ""):
    win = ctk.CTkToplevel(root)
    win.title("Create Booking")
    win.geometry("420x520")
    win.transient(root)
    win.grab_set()
    # Simple form container and helper label
    panel = ctk.CTkFrame(win)
    panel.pack(fill="both", expand=True, padx=12, pady=12)

    def label(parent, text):
        return ctk.CTkLabel(parent, text=text, anchor="w")

    # Pickup / drop fields
    pickup_var = tk.StringVar(value=prefill_pickup)
    drop_var = tk.StringVar(value=prefill_drop)
    label(panel, "Pickup:").grid(row=0, column=0, sticky="e")
    ctk.CTkEntry(panel, textvariable=pickup_var, width=220).grid(
        row=0, column=1, sticky="w", pady=6)
    label(panel, "Drop:").grid(row=1, column=0, sticky="e")
    ctk.CTkEntry(panel, textvariable=drop_var, width=220).grid(
        row=1, column=1, sticky="w", pady=6)
    label(panel, "Date:").grid(row=3, column=0, sticky="e", pady=(10, 0))
    date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    ctk.CTkEntry(panel, textvariable=date_var, width=120).grid(
        row=3, column=1, sticky="w", pady=(10, 0))

    label(panel, "Time:").grid(row=4, column=0, sticky="e", pady=(6, 0))
    hours = [f"{i:02d}" for i in range(24)]
    mins = [f"{i:02d}" for i in range(0, 60, 5)]
    time_hour_var = tk.StringVar(value=datetime.now().strftime("%H"))
    time_min_var = tk.StringVar(
        value=f"{int(datetime.now().strftime('%M')) - (int(datetime.now().strftime('%M')) % 5):02d}")
    ctk.CTkComboBox(panel, values=hours, variable=time_hour_var, width=64).grid(
        row=4, column=1, sticky="w", pady=(6, 0))
    ctk.CTkLabel(panel, text=":").grid(
        row=4, column=1, padx=(68, 0), sticky="w")
    ctk.CTkComboBox(panel, values=mins, variable=time_min_var, width=64).grid(
        row=4, column=1, padx=(80, 0), sticky="w", pady=(6, 0))

    # Available drivers list (no map)
    label(panel, "Available Drivers:").grid(
        row=5, column=0, columnspan=2, sticky="w", pady=(10, 4))
    cols = ("id", "name", "username")
    tree = ttk.Treeview(panel, columns=cols, show="headings", height=8)
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=110 if c == "id" else 140, anchor="w")
    tree.grid(row=6, column=0, columnspan=2, sticky="ew")
    panel.grid_columnconfigure(1, weight=1)

    for r in _load_drivers():
        tree.insert("", "end", values=(r["id"], r["name"], r["username"]))

    # Book button
    def do_book():
        pickup_addr = pickup_var.get().strip()
        drop_addr = drop_var.get().strip()
        date_str = date_var.get().strip()
        h = time_hour_var.get().strip().zfill(2)
        m = time_min_var.get().strip().zfill(2)
        time_str = f"{h}:{m}"

        if not all([pickup_addr, drop_addr, date_str, time_str]):
            messagebox.showwarning("Missing", "Please fill all fields.")
            return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showwarning("Invalid", "Date/Time format is invalid.")
            return

        ok, msg, booking = booking_api.create_booking(
            user["id"], pickup_addr, drop_addr, date_str, time_str)
        if not ok:
            messagebox.showerror("Booking", msg)
            return

        booking_id = booking.get("id") if booking else None

        # If the user selected a driver in the list, try to assign that driver.
        sel = tree.selection()
        if sel:
            try:
                vals = tree.item(sel[0], "values")
                driver_id = int(vals[0]) if vals else None
            except Exception:
                driver_id = None
            if driver_id and booking_id:
                # call admin.assign_driver to ensure overlap checks
                from admin import assign_driver as admin_assign
                ok2, msg2 = admin_assign(booking_id, driver_id)
                if ok2:
                    messagebox.showinfo("Booking", f"{msg} {msg2}")
                    win.destroy()
                    return
                else:
                    # show error but continue to attempt auto-assign below
                    messagebox.showwarning(
                        "Driver assign", f"Selected driver not available: {msg2}")

        # No driver selected or selected driver unavailable: try automatic assignment
        if booking_id:
            ok3, msg3, assigned_driver = booking_api.auto_assign_driver(
                booking_id)
            if ok3:
                messagebox.showinfo("Booking", f"{msg} {msg3}")
            else:
                messagebox.showinfo("Booking", f"{msg} (Note: {msg3})")
        else:
            messagebox.showinfo("Booking", msg)

        win.destroy()

    ctk.CTkButton(panel, text="Book Ride", command=do_book, height=40).grid(
        row=7, column=0, columnspan=2, pady=12, sticky="ew")


def open_menu_window(root, user):
    start_driver_coord_preloader()

    win = ctk.CTkToplevel(root)
    win.title("Menu - Map and Drivers")
    win.geometry("360x640")
    win.transient(root)
    win.grab_set()

    def on_close():
        win.destroy()
        try:
            root.deiconify()
        except Exception:
            pass
    win.protocol("WM_DELETE_WINDOW", on_close)

    top = ctk.CTkFrame(win)
    top.pack(side="top", fill="both", expand=True, padx=0, pady=0)

    mapw = TkinterMapView(top, width=860, height=320, corner_radius=8)
    mapw.pack(fill="both", expand=True)
    mapw.set_position(27.7172, 85.3240)
    mapw.set_zoom(12)

    # Route/search button overlay removed; route controls are inline in the
    # bottom overlay panel (from/to inputs and suggestions).

    # --- Smooth pan/zoom helpers ---
    def animate_pan_and_zoom(target_lat, target_lon, target_zoom=None, steps=ANIMATION_STEPS, delay=25):
        """Smoothly pan the map to (target_lat, target_lon) and optionally change zoom.

        steps: number of frames
        delay: ms between frames
        """
        try:
            # Try to get current map center and zoom
            cur_pos = mapw.get_position()  # returns (lat, lon)
            cur_lat, cur_lon = float(cur_pos[0]), float(cur_pos[1])
        except Exception:
            # Fallback: use target as start (no pan)
            cur_lat, cur_lon = target_lat, target_lon

        try:
            cur_zoom = float(mapw.get_zoom())
        except Exception:
            cur_zoom = target_zoom if target_zoom is not None else 12.0

        if target_zoom is None:
            target_zoom = cur_zoom

        # interpolate
        lat_steps = [(cur_lat + (target_lat - cur_lat) * (i / steps))
                     for i in range(1, steps + 1)]
        lon_steps = [(cur_lon + (target_lon - cur_lon) * (i / steps))
                     for i in range(1, steps + 1)]
        zoom_steps = [(cur_zoom + (target_zoom - cur_zoom) * (i / steps))
                      for i in range(1, steps + 1)]

        def frame(i=0):
            if i >= steps:
                # final exact set to avoid floating error
                try:
                    mapw.set_position(target_lat, target_lon)
                    mapw.set_zoom(target_zoom)
                except Exception:
                    pass
                return
            try:
                mapw.set_position(lat_steps[i], lon_steps[i])
                mapw.set_zoom(zoom_steps[i])
            except Exception:
                # Some map implementations may not allow fractional zoom; ignore errors
                try:
                    mapw.set_position(lat_steps[i], lon_steps[i])
                except Exception:
                    pass
            top.after(delay, lambda: frame(i + 1))

        # start animation
        frame(0)

    def center_with_vertical_offset(target_lat, target_lon, target_zoom=None, offset_px=120):
        """Compute a map center latitude that places (target_lat,target_lon) lower on the view
        by offset_px pixels (useful to keep a marker visible below top overlays).

        Returns (center_lat, center_lon, zoom)
        """
        # Choose zoom to compute meters/pixel. Use provided target_zoom when available,
        # otherwise query current map zoom.
        try:
            z = float(target_zoom) if target_zoom is not None else float(
                mapw.get_zoom())
        except Exception:
            z = float(target_zoom) if target_zoom is not None else 12.0

        # meters per pixel at latitude (approx, Web Mercator)
        lat_rad = math.radians(target_lat)
        meters_per_pixel = 156543.03392 * math.cos(lat_rad) / (2 ** z)
        meters_shift = offset_px * meters_per_pixel
        # convert meters to degrees latitude (approx): 1 deg ~ 111320 meters
        delta_deg = meters_shift / 111320.0
        # Move center to the north of target by delta_deg so target appears lower on screen
        center_lat = target_lat + delta_deg
        return center_lat, target_lon, z

    # Overlay UI that stays fixed while the map moves
    # Top-left hamburger - calls menu.open_side_menu implemented in menu.py
    overlay_top = ctk.CTkFrame(top, fg_color="transparent")
    overlay_top.place(x=8, y=8)
    overlay_top.lift()  # Bring to front
    ham_btn = ctk.CTkButton(overlay_top, text="\u2630", width=40, height=40, corner_radius=20,
                            fg_color="#1f1f1f", hover_color="#2a2a2a", text_color="white")
    ham_btn.pack()
    ham_btn.configure(command=lambda: menu.open_side_menu(top, user))

    # Bottom search panel with suggestions
    overlay_bottom = ctk.CTkFrame(top, fg_color="transparent")
    overlay_bottom.place(relx=0.5, rely=1.0, y=-8, anchor="s", relwidth=0.95)
    overlay_bottom.lift()  # Bring to front

    search_panel = ctk.CTkFrame(
        overlay_bottom, corner_radius=18, fg_color="#101010")
    search_panel.pack(fill="x")

    # Inline route controls: From / To entries and suggestion results.
    # Per request: start with an empty From field so users can type pickup explicitly
    from_var = tk.StringVar(value="")
    to_var = tk.StringVar()

    route_row = ctk.CTkFrame(search_panel, fg_color="transparent")
    route_row.pack(fill="x", padx=10, pady=8)

    from_entry = ctk.CTkEntry(route_row, textvariable=from_var,
                              placeholder_text="From (pickup)", height=36)
    from_entry.pack(side="left", padx=(0, 8))

    to_entry = ctk.CTkEntry(route_row, textvariable=to_var,
                            placeholder_text="Where to?", height=36, width=220)
    to_entry.pack(side="left", fill="x", expand=True)

    show_btn = ctk.CTkButton(route_row, text="Show route", height=36, corner_radius=12,
                             fg_color="#222", hover_color="#333", text_color="white",
                             command=lambda: draw_route(from_var.get(), to_var.get()))
    show_btn.pack(side="left", padx=(8, 2))

    # Suggestion area (populated by nominatim_search when typing in the 'To' field)
    # Do not reserve vertical space initially — pack the frame only when
    # there are results so the bottom overlay doesn't show a blank dark area.
    results_frame = ctk.CTkScrollableFrame(
        search_panel, fg_color="transparent")

    # Always-visible OK button (separate from suggestions)
    ok_button_frame = ctk.CTkFrame(search_panel, fg_color="transparent")
    ok_button_frame.pack(fill="x", padx=10, pady=(0, 6))
    ok_btn = ctk.CTkButton(ok_button_frame, text="OK", height=32, corner_radius=8,
                           fg_color="#2E4E47", hover_color="#1f6f65", text_color="white",
                           command=lambda: draw_route(from_var.get(), to_var.get()))
    ok_btn.pack(fill="x")

    # Location button — placed next to the controls to enable quick geolocation
    loc_btn = ctk.CTkButton(route_row, text="\u25CF", width=40, height=36, corner_radius=12,
                            fg_color="#1f1f1f", hover_color="#2a2a2a", text_color="#ffffff",
                            command=lambda: do_enable_location())
    loc_btn.pack(side="left", padx=(8, 2))

    # --- Context-aware popular place suggestions ---
    # Shuffle popular places for variety on each open
    random.shuffle(POPULAR_PLACES)

    # Track which entry (from/to) was last focused
    last_focused_var = tk.StringVar(value='to') # Default to 'to'
    from_entry.bind("<FocusIn>", lambda e: last_focused_var.set('from'))
    to_entry.bind("<FocusIn>", lambda e: last_focused_var.set('to'))

    def set_suggestion(place: str):
        target_var = from_var if last_focused_var.get() == 'from' else to_var
        target_var.set(place)

    # simple popular-place quick actions (useful to quickly fill 'To')
    sugg = ctk.CTkFrame(search_panel, fg_color="#101010")
    sugg.pack(fill="x", padx=10, pady=(0, 6))
    for s in POPULAR_PLACES[:4]:
        ctk.CTkButton(sugg, text=f"\u25CF  {s}", anchor="w", height=30, corner_radius=10,
                      fg_color="#1a1a1a", hover_color="#2a2a2a", text_color="#e5e5e5",
                      command=lambda t=s: set_suggestion(t)).pack(fill="x", pady=3)

    # debounce state for suggestions
    search_job = {"id": None}
    # which field the suggestions are for: 'from' or 'to'
    suggest_field = {"value": None}
    # Track which fields have been explicitly selected from suggestions
    selected_fields = {"from": False, "to": False}

    def show_results(items):
        # Clear old children (but NOT the OK button which is separate)
        for w in results_frame.winfo_children():
            w.destroy()
        # If no items, hide the results_frame to avoid blank space
        if not items:
            try:
                results_frame.pack_forget()
            except Exception:
                pass
            return

        # Ensure results_frame is visible and then populate
        try:
            results_frame.pack(fill="x", padx=10, pady=(0, 6))
        except Exception:
            pass

        for it in items:
            text = it.get("display_name")
            btn = ctk.CTkButton(results_frame, text=text, fg_color="transparent", anchor="w",
                                command=lambda t=text: on_select_suggestion(t))
            btn.pack(fill="x", pady=4)

    def on_select_suggestion(text: str):
        # Apply selection to the active field
        field = suggest_field.get("value")
        if field == 'from':
            from_var.set(text)
            selected_fields["from"] = True
        else:
            to_var.set(text)
            selected_fields["to"] = True
        show_results([])
        try:
            mapw.focus_set()
        except Exception:
            pass

    def do_suggest_search(field: str):
        q = (from_var.get() if field == 'from' else to_var.get()).strip()
        if not q:
            show_results([])
            return
        items = nominatim_search(q)
        # Keep only suggestions that start with the typed prefix when possible
        starts = [it for it in items if it.get(
            'display_name', '').lower().startswith(q.lower())]
        items_to_show = starts if starts else items
        # Do not auto-fill the entry with suggestions; only display suggestions
        show_results(items_to_show)

    def debounced_search_for(field: str, event=None):
        # schedule search for a specific field
        try:
            if search_job["id"]:
                top.after_cancel(search_job["id"])
        except Exception:
            pass
        suggest_field["value"] = field
        search_job["id"] = top.after(250, lambda: do_suggest_search(field))

    # Bind both entries to suggestion behavior
    from_entry.bind("<KeyRelease>", lambda e: debounced_search_for('from', e))
    to_entry.bind("<KeyRelease>", lambda e: debounced_search_for('to', e))
    # Pressing Enter in the To field will confirm the current text and draw the route

    def on_to_enter(event=None):
        txt = to_var.get().strip()
        if not txt:
            return
        # clear suggestions and draw
        show_results([])
        draw_route(from_var.get(), txt)
        try:
            mapw.focus_set()
        except Exception:
            pass

    to_entry.bind('<Return>', on_to_enter)

    # Remember markers
    state = {"user_marker": None, "driver_markers": [],
             "nearby_after_id": None, "last_center": None, "last_zoom": None}

    def draw_route(from_addr: str, to_addr: str):
        """Geocode both endpoints, request a route, draw it on the map and show markers."""
        if not to_addr:
            messagebox.showwarning('Route', 'Please enter a destination.')
            return
        # geocode both endpoints
        pickup = from_addr.strip() or user.get('address', '')
        pcoords = geocode(pickup)
        dcoords = geocode(to_addr.strip())
        if not pcoords or not dcoords:
            messagebox.showwarning(
                'Route', 'Could not geocode pickup or destination.')
            return

        plat, plon = pcoords[0], pcoords[1]
        dlat, dlon = dcoords[0], dcoords[1]

        path = get_route_coords(plat, plon, dlat, dlon)
        # clear existing path/markers
        try:
            if state.get('current_path'):
                try:
                    mapw.delete(state['current_path'])
                except Exception:
                    pass
                state['current_path'] = None
        except Exception:
            pass
        try:
            if state.get('pickup_marker'):
                try:
                    state['pickup_marker'].delete()
                except Exception:
                    pass
                state['pickup_marker'] = None
        except Exception:
            pass
        try:
            if state.get('drop_marker'):
                try:
                    state['drop_marker'].delete()
                except Exception:
                    pass
                state['drop_marker'] = None
        except Exception:
            pass

        # set markers
        try:
            state['pickup_marker'] = mapw.set_marker(plat, plon, text='Pickup')
        except Exception:
            state['pickup_marker'] = None
        try:
            state['drop_marker'] = mapw.set_marker(dlat, dlon, text='Drop')
        except Exception:
            state['drop_marker'] = None

        if path:
            try:
                state['current_path'] = mapw.set_path(
                    path, width=4, color='#0066ff')
            except Exception:
                state['current_path'] = None

        # adjust view to fit route: center midpoint and choose zoom by distance
        try:
            dist_km = haversine(plat, plon, dlat, dlon)
            mid_lat = (plat + dlat) / 2.0
            mid_lon = (plon + dlon) / 2.0
            # heuristic zoom selection
            if dist_km > 200:
                z = 6
            elif dist_km > 50:
                z = 8
            elif dist_km > 10:
                z = 11
            else:
                z = 13
            center_lat, center_lon, _ = center_with_vertical_offset(
                mid_lat, mid_lon, target_zoom=z, offset_px=120)
            animate_pan_and_zoom(center_lat, center_lon, target_zoom=z)
        except Exception:
            pass
        try:
            show_drivers_section()
            pass
        except Exception:
            pass

    # Inline drivers panel (created on demand)
    def show_drivers_section():
        # Create or refresh the drivers panel listing nearby drivers for the pickup
        try:
            pickup_addr = from_var.get().strip()
            if not pickup_addr:
                return
            pcoords = geocode(pickup_addr)
            if not pcoords:
                return
            plat, plon = pcoords[0], pcoords[1]
        except Exception:
            return

        # create panel if not exists
        if not state.get('drivers_panel'):
            dp = ctk.CTkFrame(search_panel, fg_color="#0f0f0f")
            dp.pack(fill="x", padx=10, pady=(6, 8))
            state['drivers_panel'] = dp
        else:
            dp = state['drivers_panel']
            for w in dp.winfo_children():
                w.destroy()

        # columns: id, name, dist_km, address
        cols = ("id", "name", "dist_km", "address")
        tree = ttk.Treeview(dp, columns=cols, show="headings", height=6)
        for c in cols:
            tree.heading(c, text=c.capitalize())
            tree.column(c, width=120 if c == 'id' else 180, anchor='w')
        tree.pack(fill="both", expand=True, pady=(4, 6))

        # collect drivers from preloaded cache or load fresh
        source = []
        if not source:
            rows = _load_drivers()
            for r in rows:
                addr = r["address"] if isinstance(
                    r, dict) else r['address']
                coords = geocode(addr)
                if coords:
                    source.append(
                        (r['id'], r["name"], coords[0], coords[1], addr))

        drivers_list = []
        for item in source:
            did, name, dlat, dlon, addr = item
            dist = haversine(plat, plon, dlat, dlon)
            drivers_list.append((did, name, dist, addr))

        drivers_list.sort(key=lambda x: x[2])

        for did, name, dist, addr in drivers_list[:10]:
            tree.insert("", "end", values=(did, name, f"{dist:.2f} km", addr))

        btn_row = ctk.CTkFrame(dp, fg_color="transparent")
        btn_row.pack(fill="x")

        def do_book_inline():
            sel = tree.selection()
            selected_driver = None
            if sel:
                try:
                    vals = tree.item(sel[0], 'values')
                    selected_driver = int(vals[0])
                except Exception:
                    selected_driver = None

            pickup_addr = from_var.get().strip()
            drop_addr = to_var.get().strip()
            if not pickup_addr or not drop_addr:
                messagebox.showwarning(
                    'Booking', 'Pickup and drop must be set')
                return
            # simple immediate booking: today's date and current time
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M')

            ok, msg, booking = booking_api.create_booking(
                user['id'], pickup_addr, drop_addr, date_str, time_str)
            if not ok:
                messagebox.showerror('Booking', msg)
                return
            booking_id = booking.get('id') if booking else None

            if selected_driver and booking_id:
                try:
                    from admin import assign_driver as admin_assign
                    ok2, msg2 = admin_assign(booking_id, selected_driver)
                    if ok2:
                        messagebox.showinfo('Booking', f'{msg} {msg2}')
                    else:
                        messagebox.showwarning(
                            'Driver assign', f'Selected driver not available: {msg2}')
                        # fallback to auto-assign
                        ok3, msg3, drv = booking_api.auto_assign_driver(
                            booking_id)
                        messagebox.showinfo('Booking', f'{msg} (Note: {msg3})')
                except Exception:
                    # fallback
                    ok3, msg3, drv = booking_api.auto_assign_driver(booking_id)
                    messagebox.showinfo('Booking', f'{msg} (Note: {msg3})')
            else:
                if booking_id:
                    ok3, msg3, drv = booking_api.auto_assign_driver(booking_id)
                    messagebox.showinfo('Booking', f'{msg} (Note: {msg3})')
            # refresh drivers panel to reflect any assignment
            show_drivers_section()

        ctk.CTkButton(btn_row, text='Book with selected driver', command=do_book_inline,
                      fg_color='#2266aa').pack(side='left', padx=6, pady=6)
        ctk.CTkButton(btn_row, text='Auto-assign', command=do_book_inline,
                      fg_color='#228833').pack(side='left', padx=6, pady=6)

    def do_search(text: str):
        text = text.strip()
        if not text:
            return
        coords = geocode(text)
        if coords:
            lat, lon = coords
            # Smooth pan and zoom to searched location but offset vertically so marker is
            # not hidden under the top search overlay.
            center_lat, center_lon, z = center_with_vertical_offset(
                lat, lon, target_zoom=14, offset_px=120)
            animate_pan_and_zoom(center_lat, center_lon, target_zoom=z)
            mapw.set_marker(lat, lon, text="Search")
        else:
            messagebox.showwarning("Search", "Location not found.")

    def on_location_success(lat, lon):
        try:
            animate_pan_and_zoom(lat, lon, target_zoom=13)
            if state.get('user_marker'):
                state['user_marker'].delete()
            state['user_marker'] = mapw.set_marker(lat, lon, text=f"{user['name']}")
            update_driver_markers_on_map(lat, lon)
        except Exception:
            pass

    def on_location_fail(message):
        messagebox.showinfo('Location', message)

    def do_enable_location():
        enable_location(on_location_success, on_location_fail)

    def update_driver_markers_on_map(center_lat, center_lon):
        try:
            zoom = float(mapw.get_zoom())
        except Exception:
            zoom = 12.0

        def on_driver_results(marker_data):
            # This is the callback that receives cluster/single driver data
            for m in state.get("driver_markers", []):
                try:
                    m.delete()
                except Exception:
                    pass
            state["driver_markers"] = []
            for md in marker_data:
                try:
                    if md['type'] == 'cluster':
                        marker = mapw.set_marker(
                            md['lat'], md['lon'], text=f"{md['count']} drivers")
                        state["driver_markers"].append(marker)
                    else:
                        marker = mapw.set_marker(
                            md['lat'], md['lon'], text=f"{md['name']} ({md['dist']:.1f} km)")
                        state["driver_markers"].append(marker)
                except Exception:
                    pass

        show_nearby_drivers(top, center_lat, center_lon, zoom, on_driver_results)
