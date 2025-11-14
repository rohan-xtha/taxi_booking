import booking as booking_api
import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import List, Dict
from db import get_conn
import threading
from map import geocode, haversine

# Performance / tuning constants
MAX_DRIVER_MARKERS = 10  # maximum markers to show for drivers
NEARBY_DEBOUNCE_MS = 250  # debounce nearby driver lookups


# Preloaded driver coordinates to reduce lag
driver_coords_preloaded = []

def list_bookings_by_driver(driver_id: int) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""SELECT * FROM bookings
                   WHERE driver_id=? AND status!='cancelled'""", (driver_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _load_drivers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, username, address FROM users WHERE role='driver' ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows  # list[sqlite3.Row]


def _preload_driver_coords():
    global driver_coords_preloaded
    rows = _load_drivers()
    tmp = []
    for r in rows:
        addr = r["address"] if isinstance(r, dict) else r["address"]
        if not addr:
            continue
        coords = geocode(addr)
        if coords:
            lat, lon = coords
            tmp.append((r["id"], r["name"], lat, lon, addr))
    driver_coords_preloaded = tmp


def start_driver_coord_preloader():
    """Starts a background thread to preload driver coordinates."""
    threading.Thread(target=_preload_driver_coords, daemon=True).start()


def show_nearby_drivers(parent_widget, ulat, ulon, map_zoom, on_results_callback, km=3.0):
    """
    Finds nearby drivers, clusters them if necessary, and calls a callback with marker data.
    This function is debounced to prevent excessive lookups.
    """
    # debounce state is stored on the parent widget
    state = getattr(parent_widget, "_driver_lookup_state", {"id": None})
    setattr(parent_widget, "_driver_lookup_state", state)

    prev = state.get("id")
    if prev:
        try:
            parent_widget.after_cancel(prev)
        except Exception:
            pass

    def do_lookup():
        source = list(
            driver_coords_preloaded) if driver_coords_preloaded else []
        if not source:
            rows = _load_drivers()
            for r in rows:
                addr = r.get("address") if isinstance(
                    r, dict) else r["address"]
                coords = geocode(addr)
                if coords:
                    source.append(
                        (r["id"], r.get("name"), coords[0], coords[1], addr))

        # collect nearby candidates (limit to 200 for clustering performance)
        nearby = []
        for item in source:
            _, name, dlat, dlon, _ = item
            dist = haversine(ulat, ulon, dlat, dlon)
            if dist <= km:
                nearby.append((dist, name, dlat, dlon))

        nearby.sort(key=lambda x: x[0])
        nearby = nearby[:200]

        # If only a few drivers, show them directly
        if len(nearby) <= MAX_DRIVER_MARKERS:
            results = [{'type': 'single', 'dist': dist, 'lat': dlat, 'lon': dlon, 'name': name}
                       for dist, name, dlat, dlon in nearby][:MAX_DRIVER_MARKERS]
            parent_widget.after(0, lambda: on_results_callback(results))
            return

        # Otherwise cluster in background to avoid blocking UI
        def cluster_worker(nearby_list, cur_zoom):
            try:
                import numpy as _np
                from sklearn.cluster import DBSCAN as _DBSCAN
            except ImportError:
                # clustering libs not available — fallback to showing top N
                results = [{'type': 'single', 'dist': dist, 'lat': dlat, 'lon': dlon, 'name': name}
                           for dist, name, dlat, dlon in nearby_list][:MAX_DRIVER_MARKERS]
                parent_widget.after(0, lambda: on_results_callback(results))
                return

            # larger eps at low zooms -> clusters merge; smaller eps at high zooms
            eps_km = max(0.2, 1.2 * (13.0 / max(1.0, cur_zoom)))
            coords = [(dlat, dlon) for _, _, dlat, dlon in nearby_list]
            labels = []
            try:
                db = _DBSCAN(eps=eps_km / 6371.0088, min_samples=2,
                             algorithm='ball_tree', metric='haversine')
                labels = db.fit_predict(_np.radians(coords))
            except Exception:
                labels = [-1] * len(coords)

            clusters = {}
            singles = []
            for i, lab in enumerate(labels):
                dist, name, dlat, dlon = nearby_list[i]
                if lab == -1:
                    singles.append((dist, name, dlat, dlon))
                else:
                    clusters.setdefault(lab, []).append(
                        (dist, name, dlat, dlon))

            markers_data = []
            for members in clusters.values():
                cnt = len(members)
                avg_lat = sum(m[2] for m in members) / cnt
                avg_lon = sum(m[3] for m in members) / cnt
                markers_data.append(
                    {'type': 'cluster', 'count': cnt, 'lat': avg_lat, 'lon': avg_lon})
            for s in singles[:MAX_DRIVER_MARKERS]:
                dist, name, dlat, dlon = s
                markers_data.append(
                    {'type': 'single', 'name': name, 'lat': dlat, 'lon': dlon, 'dist': dist})

            parent_widget.after(0, lambda: on_results_callback(markers_data))

        threading.Thread(target=cluster_worker, args=(
            nearby, map_zoom), daemon=True).start()

    state["id"] = parent_widget.after(NEARBY_DEBOUNCE_MS, do_lookup)

# ---- Driver UI (moved from login.py) ----


def show_text(parent, title, text):
    dlg = ctk.CTkToplevel(parent)
    dlg.title(title)
    t = ctk.CTkTextbox(dlg, width=450, height=250)
    t.pack(fill="both", expand=True, padx=12, pady=12)
    t.insert("1.0", text)
    t.configure(state="disabled")
    ctk.CTkButton(dlg, text="Close", command=dlg.destroy).pack(pady=(0, 12))


def open_driver_window(root, user):
    win = ctk.CTkToplevel(root)
    win.title("Driver Dashboard")
    win.geometry("800x500")
    win.grab_set()

    # Dark header
    header_frame = ctk.CTkFrame(win, fg_color="#0E0E0E", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_label = ctk.CTkLabel(
        header_frame,
        text="Driver Dashboard",
        text_color="white",
        font=("Helvetica", 24, "bold")
    )
    header_label.pack(pady=12)

    # White content frame
    content_frame = ctk.CTkFrame(win, fg_color="white")
    content_frame.pack(fill="both", expand=True, padx=0, pady=0)

    # Inner content with padding
    inner_frame = ctk.CTkFrame(content_frame, fg_color="white")
    inner_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Title with driver name
    title_label = ctk.CTkLabel(
        inner_frame,
        text=f"Welcome, {user.get('name', 'Driver')}!",
        text_color="#0E0E0E",
        font=("Helvetica", 16, "bold")
    )
    title_label.pack(pady=(0, 12))

    frame = ctk.CTkFrame(inner_frame, fg_color="white")
    frame.pack(fill="both", expand=True)

    cols = ("id", "customer_id", "pickup", "dropoff", "date", "time", "status")

    # Add scrollbar for the treeview
    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")

    tree = ttk.Treeview(frame, columns=cols, show="headings",
                        height=12, yscrollcommand=scrollbar.set)
    scrollbar.config(command=tree.yview)

    for c in cols:
        tree.heading(c, text=c.replace("_", " ").capitalize())
        tree.column(c, width=100 if c in ("id", "customer_id",
                    "date", "time", "status") else 180, anchor="w")
    tree.pack(fill="both", expand=True)

    btn_frame = ctk.CTkFrame(inner_frame, fg_color="white")
    btn_frame.pack(fill="x", pady=(12, 0))

    def load_bookings():
        for i in tree.get_children():
            tree.delete(i)
        rows = list_bookings_by_driver(user["id"])
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

    def cancel_selected_driver():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(
                "No selection", "Please select a booking to cancel.")
            return
        vals = tree.item(sel[0], "values")
        bid = int(vals[0])
        ok, msg = booking_api.cancel_booking(bid)
        if ok:
            messagebox.showinfo("Cancelled", msg)
            load_bookings()
        else:
            messagebox.showerror("Error", msg)

    refresh_btn = ctk.CTkButton(
        btn_frame,
        text="🔄 Refresh",
        command=load_bookings,
        fg_color="#2E4E47",
        hover_color="#1f6f65",
        text_color="white",
        font=("Helvetica", 14, "bold"),
        height=45,
        corner_radius=12
    )
    refresh_btn.pack(side="left", padx=(0, 8))

    view_btn = ctk.CTkButton(
        btn_frame,
        text="👁️ View",
        command=view_selected,
        fg_color="#2E4E47",
        hover_color="#1f6f65",
        text_color="white",
        font=("Helvetica", 14, "bold"),
        height=45,
        corner_radius=12
    )
    view_btn.pack(side="left", padx=(0, 8))

    complete_btn = ctk.CTkButton(
        btn_frame,
        text="✓ Mark Completed",
        command=mark_complete,
        fg_color="#2E4E47",
        hover_color="#1f6f65",
        text_color="white",
        font=("Helvetica", 14, "bold"),
        height=45,
        corner_radius=12
    )
    complete_btn.pack(side="right", padx=(0, 8))

    cancel_btn = ctk.CTkButton(
        btn_frame,
        text="✗ Cancel Booking",
        command=cancel_selected_driver,
        fg_color="#d9534f",
        hover_color="#c9302c",
        text_color="white",
        font=("Helvetica", 14, "bold"),
        height=45,
        corner_radius=12
    )
    cancel_btn.pack(side="right")

    load_bookings()


def view_driver_trips(parent, user):
    rows = list_bookings_by_driver(user["id"])
    if not rows:
        messagebox.showinfo("My Trips", "No assigned trips.")
        return
    text = "\n".join([f"ID {b['id']} | {b['date']} {b['time']} {b['pickup']} -> {b['dropoff']} "
                      f"| {b['status']}" for b in rows])
    show_text(parent, "My Trips", text)
