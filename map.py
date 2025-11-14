import json
import math
import queue
import socket
import http.server
import threading
import webbrowser
from typing import Optional
from urllib import request as urlrequest, parse as urlparse

# Simple in-memory cache for geocoding lookups to avoid repeated network calls
GEOCODE_CACHE: dict = {}
GEOCODE_LOCK = threading.Lock()


def nominatim_search(q: str, limit: int = 6):
    """Query Nominatim for place suggestions. Returns list of dicts with display_name, lat, lon.
    Filters results to only show locations in Nepal."""
    try:
        # Search with viewbox preference (not strict bounds) for Nepal
        # Nepal roughly: lat 26.0-30.5, lon 80.0-88.3
        url = f"https://nominatim.openstreetmap.org/search?{urlparse.urlencode({'q': q, 'format': 'json', 'limit': limit, 'viewbox': '80.0,30.5,88.3,26.0'})}"
        req = urlrequest.Request(
            url, headers={"User-Agent": "taxi-booking-app/1.0"})
        with urlrequest.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        results = []
        for r in data:
            lat = float(r.get('lat'))
            lon = float(r.get('lon'))
            display_name = r.get('display_name', '')

            # Only include if Nepal is in the display name OR coordinates are within Nepal bounds (with 1 degree margin)
            if 'Nepal' in display_name or (25.0 <= lat <= 31.5 and 79.0 <= lon <= 89.3):
                results.append({
                    'display_name': display_name,
                    'lat': lat,
                    'lon': lon
                })
        return results
    except Exception:
        return []


def geocode(addr: str):
    # Use cache to avoid repeated network requests for the same address
    if not addr:
        return None
    key = addr.strip().lower()
    with GEOCODE_LOCK:
        if key in GEOCODE_CACHE:
            return GEOCODE_CACHE[key]
    try:
        q = urlparse.urlencode({"q": addr, "format": "json", "limit": 1})
        url = f"https://nominatim.openstreetmap.org/search?{q}"
        req = urlrequest.Request(
            url, headers={"User-Agent": "taxi-booking-app/1.0"})
        with urlrequest.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data:
            return None
        coords = (float(data[0]["lat"]), float(data[0]["lon"]))
        with GEOCODE_LOCK:
            GEOCODE_CACHE[key] = coords
        return coords
    except Exception:
        return None


def get_route_coords(slat, slon, dlat, dlon):
    """Query OSRM public demo server to get a route geometry (list of (lat,lon))."""
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{slon},{slat};{dlon},{dlat}?overview=full&geometries=geojson"
        req = urlrequest.Request(
            url, headers={"User-Agent": "taxi-booking-app/1.0"})
        with urlrequest.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        routes = data.get('routes')
        if not routes:
            return None
        coords = routes[0].get('geometry', {}).get('coordinates', [])
        # coords are [lon, lat] pairs
        path = [(float(lat), float(lon)) for lon, lat in coords]
        return path
    except Exception:
        return None


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def enable_location(on_success_callback, on_fail_callback):
    """
    Tries to get user's location.
    - on_success_callback(lat, lon): Called with coordinates on success.
    - on_fail_callback(message): Called with an error message on failure.
    """
    # First try: request high-accuracy browser geolocation via a temporary local HTTP server
    coords_q: "queue.Queue[Optional[tuple]]" = queue.Queue()

    class GeoHandler(http.server.BaseHTTPRequestHandler):
        def _set_json(self, code=200):
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

        def do_GET(self):
            if self.path in ('/', '/geo'):
                # Serve a minimal HTML page that requests geolocation and POSTs it back
                html = """<!doctype html>
<html><head><meta charset='utf-8'><title>Share location</title></head>
<body>
<h3>This page will request your location to share with the Taxi app.</h3>
<p>Please allow the location prompt in your browser.</p>
<script>
function postPos(lat, lon){
  fetch('/loc', {method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({lat:lat, lon:lon})});
  document.body.innerHTML += '<p>Location sent — you can close this tab.</p>';
}
if(navigator && navigator.geolocation){
  navigator.geolocation.getCurrentPosition(function(pos){postPos(pos.coords.latitude, pos.coords.longitude);}, function(err){document.body.innerHTML += '<p>Unable to get location: '+err.message+'</p>';}, {enableHighAccuracy:true, timeout:15000});
} else { document.body.innerHTML += '<p>Geolocation not supported in your browser.</p>'; }
</script>
</body></html>"""
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == '/loc':
                length = int(self.headers.get('content-length', 0))
                data = self.rfile.read(length).decode('utf-8')
                try:
                    obj = json.loads(data)
                    lat = float(obj.get('lat'))
                    lon = float(obj.get('lon'))
                    # Put coords into queue for the main thread
                    try:
                        coords_q.put_nowait((lat, lon))
                    except Exception:
                        pass
                    self._set_json(200)
                    self.wfile.write(json.dumps(
                        {'ok': True}).encode('utf-8'))
                except Exception:
                    self._set_json(400)
                    self.wfile.write(json.dumps(
                        {'ok': False}).encode('utf-8'))
            else:
                self.send_error(404)

        def log_message(self, format, *args):
            # silence logging to stderr
            return

    def start_geo_server(port=0):
        # find free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            port = s.getsockname()[1]
        server = http.server.HTTPServer(('127.0.0.1', port), GeoHandler)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, port

    def poll_for_coords(server, root_widget, timeout_ms=15000, interval_ms=200):
        waited = 0

        def poll():
            nonlocal waited
            try:
                latlon = coords_q.get_nowait()
            except queue.Empty:
                latlon = None

            if latlon:
                # received coords
                lat, lon = latlon
                on_success_callback(lat, lon)
                try:
                    server.shutdown()
                except Exception:
                    pass
                return

            waited += interval_ms
            if waited >= timeout_ms:
                # timeout: fall back to IP-based
                try:
                    server.shutdown()
                except Exception:
                    pass
                try:
                    req = urlrequest.Request(
                        'http://ip-api.com/json', headers={'User-Agent': 'taxi-booking-app/1.0'})
                    with urlrequest.urlopen(req, timeout=8) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                    if data.get('status') == 'success':
                        lat, lon = float(data['lat']), float(data['lon'])
                        on_success_callback(lat, lon)
                        return
                except Exception:
                    pass
                on_fail_callback('Could not detect location. You can search manually.')
                return
            root_widget.after(interval_ms, poll)

        poll()

    def run_location_flow(root_widget):
        try:
            server, port = start_geo_server()
            url = f'http://127.0.0.1:{port}/geo'
            webbrowser.open(url)
            poll_for_coords(server, root_widget)
        except Exception:
            # fallback: IP-based approximate geolocation
            try:
                req = urlrequest.Request(
                    'http://ip-api.com/json', headers={'User-Agent': 'taxi-booking-app/1.0'})
                with urlrequest.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                if data.get('status') == 'success':
                    lat, lon = float(data['lat']), float(data['lon'])
                    on_success_callback(lat, lon)
                    return
            except Exception:
                pass
            on_fail_callback('Location detection failed. You can search manually.')

    # The root widget is needed for `after` calls.
    # We need to find it. A bit of a hack.
    from tkinter import _get_default_root
    root = _get_default_root()
    if root:
        threading.Thread(target=lambda: run_location_flow(root), daemon=True).start()
    else:
        on_fail_callback("Could not find root window for location service.")