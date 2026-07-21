"""Map view — right column. Interactive Leaflet map (Canada + Arctic) embedded
via QWebEngineView + QWebChannel, ported from the github/qtmap example
(radiolab9, MIT). Event dots are fed by MainWindow's ZMQ subscriber
(ui/zmq_client.py) and plotted at their coordinates, colored by severity.
Single-clicking a marker focuses the Events Feed row for that incident;
double-clicking opens it in the shared PopupGroup (see MainWindow).

For events carrying a target_lat/target_lon (predicted-movement events --
drones, mobs, tank columns with a known destination), the origin marker
stays a plain severity-colored dot; a static dashed path + arrowhead is
drawn from it to that real destination. Events with only a heading_deg and
no named destination fall back to a short fixed-length line in that
direction instead. There is no animation -- it's been added and removed a
couple of times now chasing UI lag reports; even after fixing the actual
lag cause (common/debug_controller.py forcing a flush on every event
print -- see project memory) it was still laggy, so it's staying off.
Paths render on a shared Leaflet Canvas layer (L.polyline with an explicit
`renderer`), cheap even with dozens on screen at once. Origin dots are real
DOM markers (L.marker/L.divIcon), not canvas-rendered like the paths --
canvas circleMarker hit-testing turned out unreliable for clicks here, and a
DOM marker also guarantees it renders above the paths (Leaflet's markerPane
always sits above the paths' overlayPane) regardless of add order.

Bundled assets live in ui/map_assets/ (Leaflet 1.9.4 + Canada province
outline). Tiles are fetched live from CartoDB's CDN — this needs internet at
demo time; the qtmap example's offline tile-server story (see its README)
was never actually wired up in that repo, so it wasn't ported here.
"""
import os

from PyQt5.QtCore import QObject, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from common.severity_colors import color_for_level

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_assets")
_CANADA_GEOJSON_PATH = os.path.join(_ASSETS_DIR, "canada.geojson")
_GENERATED_HTML_PATH = os.path.join(_ASSETS_DIR, "_map_view.html")


def _build_map_html() -> str:
    with open(_CANADA_GEOJSON_PATH) as f:
        canada_geojson = f.read()

    # leaflet.js/css load as plain local files via relative <script src>/<link>
    # — that works fine under file://. GeoJSON can't use the equivalent (a
    # runtime fetch/XHR): Chromium blocks XHR-to-local-file under file:// by
    # default and silently drops the response, which is why the outline never
    # rendered in the qtmap original this was ported from. Inlining it as a JS
    # literal sidesteps that.
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="leaflet/leaflet.css">
<style>
html, body {{ margin: 0; padding: 0; height: 100%; }}
#map {{ height: 100%; width: 100%; background: #1c2b3a; }}
.leaflet-control-attribution {{ display: none; }}
</style>
</head>
<body>
<div id="map"></div>
<script src="leaflet/leaflet.js"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
var CANADA_GEOJSON = {canada_geojson};
var map;
var canvasRenderer;  // shared Canvas layer for origin dots + paths -- see module docstring
var markers = {{}};
var markerMeta = {{}};  // eventId -> {{baseDiameter, color, typeStyle}}, used to rescale on zoom
var predictedPaths = {{}};  // trackKey -> {{path: L.Polyline, arrowTip: L.Marker}} -- static, no animation
var pyHandler = null;

// Dots are a fixed screen-pixel size regardless of zoom (like any DOM
// marker) -- zooming in to get a better angle to click one doesn't actually
// make it any bigger, which reads as the dot "running away" from the
// cursor. Growing it a bit with zoom (relative to the initial view) fixes
// that without makings dots absurdly huge at max zoom (capped below).
var REFERENCE_ZOOM = 4;  // matches initMap()'s initial setView zoom

function scaleForZoom(zoom) {{
    return Math.min(1 + Math.max(0, zoom - REFERENCE_ZOOM) * 0.2, 3.5);
}}

function rescaleMarkers() {{
    var scale = scaleForZoom(map.getZoom());
    for (var eventId in markerMeta) {{
        var marker = markers[eventId];
        if (!marker) {{ continue; }}
        var meta = markerMeta[eventId];
        marker.setIcon(dotIcon(meta.baseDiameter * scale, meta.color, meta.typeStyle));
    }}
}}

new QWebChannel(qt.webChannelTransport, function(channel) {{
    pyHandler = channel.objects.pyHandler;
}});

function initMap() {{
    map = L.map('map', {{
        zoomControl: true,
        crs: L.CRS.EPSG3857
    }}).setView([62.0, -98.0], 4);

    canvasRenderer = L.canvas({{ padding: 0.5 }});

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: ''
    }}).addTo(map);

    L.geoJSON(CANADA_GEOJSON, {{
        style: {{ color: '#5a86b8', weight: 2, opacity: 0.9, fillColor: '#1c2b3a', fillOpacity: 0.15 }}
    }}).addTo(map);

    map.on('click', function(e) {{
        if (pyHandler) {{
            pyHandler.onMapClick(e.latlng.lat, e.latlng.lng);
        }}
    }});
    map.on('zoomend', rescaleMarkers);
}}

// Origin dots used to be canvas-rendered (L.circleMarker on a shared
// renderer) for cheap rendering with many on screen -- but canvas hit-testing
// turned out unreliable here (clicks squarely on a dot were falling through
// to the plain map-click handler instead of the marker's), and canvas layers
// live in the z-order below the marker pane, so a marker pane icon (e.g. the
// arrowhead) could in principle sit above them too. A real L.marker/divIcon
// uses the browser's own DOM hit-testing (exact) and always renders in
// Leaflet's markerPane, above the overlayPane paths/GeoJSON regardless of
// add order -- worth the small DOM cost at this scale (dozens, not hundreds).
// Shape per event type, not a glyph/emoji -- Qt's native widgets already
// can't render emoji reliably (tofu boxes, see events_feed.py), and Chromium
// under QWebEngine is no safer bet either (Linux Chromium still depends on a
// system emoji font being installed). Plain CSS shapes (clip-path/border-
// radius) have no font dependency at all -- same reasoning as the existing
// pure-CSS arrowhead triangle below.
var TYPE_SHAPE = {{
    photo: 'border-radius:3px;',
    video: 'clip-path:polygon(15% 0%,15% 100%,100% 50%);',
    audio: 'border-radius:50%;',
    fft: 'clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);',
    float_sequence: 'clip-path:polygon(25% 0%,75% 0%,100% 50%,75% 100%,25% 100%,0% 50%);'
}};
var DEFAULT_SHAPE = 'border-radius:50%;';

function dotIcon(diameterPx, color, typeStyle) {{
    return L.divIcon({{
        className: 'event-marker',
        html: '<div style="width:' + diameterPx + 'px;height:' + diameterPx + 'px;' +
              'background:' + color + ';border:2px solid #ffffff;box-sizing:border-box;' +
              (typeStyle || DEFAULT_SHAPE) + '"></div>',
        iconSize: [diameterPx, diameterPx],
        iconAnchor: [diameterPx / 2, diameterPx / 2]
    }});
}}

function darkenColor(hex, factor) {{
    var c = (hex || '#ffffff').replace('#', '');
    if (c.length !== 6) {{ return hex; }}
    var r = Math.round(parseInt(c.substring(0, 2), 16) * factor);
    var g = Math.round(parseInt(c.substring(2, 4), 16) * factor);
    var b = Math.round(parseInt(c.substring(4, 6), 16) * factor);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
}}

function arrowHeadIcon(headingDeg) {{
    return L.divIcon({{
        className: 'event-marker',
        html: '<div style="width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;' +
              'border-bottom:14px solid #ffe066;transform:rotate(' + headingDeg + 'deg);filter:drop-shadow(0 0 2px #000);"></div>',
        iconSize: [14, 14],
        iconAnchor: [7, 7]
    }});
}}

function bearingTo(lat1, lng1, lat2, lng2) {{
    var dLat = lat2 - lat1;
    var dLng = (lng2 - lng1) * Math.cos(lat1 * Math.PI / 180);
    return (Math.atan2(dLng, dLat) * 180 / Math.PI + 360) % 360;
}}

// Many events legitimately share the same (or near-identical) real-world
// coordinates -- multiple sensors on the same city block, repeat seismic
// readings at one station, etc. Rendered literally on top of each other
// they're indistinguishable and unclickable past the first one. This keeps
// the *reported* coordinate untouched everywhere else (map clicks, popups,
// focusMarker) and only nudges the dot actually drawn, spreading repeats
// into a small ring around the true point.
var locationCounts = {{}};

function spreadLocation(lat, lng) {{
    var key = lat.toFixed(3) + ',' + lng.toFixed(3);
    var index = locationCounts[key] || 0;
    locationCounts[key] = index + 1;
    if (index === 0) {{
        return [lat, lng];
    }}
    // golden-angle spacing so repeats don't line up radially into each
    // other as the ring grows; radius steps out every 8 markers at one spot.
    var angle = index * 137.5 * Math.PI / 180;
    var radius = 0.0006 * (1 + Math.floor((index - 1) / 8));
    var latScale = Math.max(0.15, Math.cos(lat * Math.PI / 180));
    return [lat + Math.cos(angle) * radius, lng + Math.sin(angle) * radius / latScale];
}}

function addOrUpdateMarker(eventId, lat, lng, color, type_, headingDeg, speedKmh, trackId, targetLat, targetLng) {{
    if (markers[eventId]) {{
        map.removeLayer(markers[eventId]);
    }}
    clearPath(eventId);  // clean up a standalone (no trackId) path previously keyed by this id

    var spread = spreadLocation(lat, lng);
    lat = spread[0];
    lng = spread[1];

    var hasTarget = (targetLat !== null && targetLat !== undefined);
    var hasHeading = hasTarget || (headingDeg !== null && headingDeg !== undefined);

    // origin event always stays where it happened, with its own dot -- but
    // when it's the origin of a predicted path, it's dimmed down so the
    // path/arrow reads clearly against it.
    var originColor = hasHeading ? darkenColor(color, 0.5) : color;
    var typeStyle = TYPE_SHAPE[type_] || DEFAULT_SHAPE;
    var baseDiameter = hasHeading ? 11 : 14;
    markerMeta[eventId] = {{baseDiameter: baseDiameter, color: originColor, typeStyle: typeStyle}};
    var diameter = baseDiameter * scaleForZoom(map.getZoom());
    var marker = L.marker([lat, lng], {{icon: dotIcon(diameter, originColor, typeStyle)}}).addTo(map);
    marker.on('click', function() {{
        if (pyHandler) {{ pyHandler.onMarkerClick(eventId); }}
    }});
    marker.on('dblclick', function(e) {{
        L.DomEvent.stopPropagation(e);
        if (pyHandler) {{ pyHandler.onMarkerDoubleClick(eventId); }}
    }});
    markers[eventId] = marker;

    if (hasHeading) {{
        // trackId (tag_id) ties repeat detections of the same tracked object
        // together: a fresh detection re-anchors that object's predicted
        // path here instead of leaving the old one stuck at a stale sighting.
        var trackKey = trackId || eventId;
        clearPath(trackKey);

        var endLat, endLng, arrowHeading;
        if (hasTarget) {{
            // real destination known -- path runs the actual distance to it,
            // and the arrow direction is derived from these two points
            // (never authored separately, so it can't drift out of sync).
            endLat = targetLat;
            endLng = targetLng;
            arrowHeading = bearingTo(lat, lng, targetLat, targetLng);
        }} else {{
            // no named destination -- short heading-only line, a generic
            // "this is moving in roughly this direction" cue.
            var rad = headingDeg * Math.PI / 180;
            var latScale = Math.max(0.15, Math.cos(lat * Math.PI / 180));
            var pathLenDeg = 0.35;
            endLat = lat + Math.cos(rad) * pathLenDeg;
            endLng = lng + Math.sin(rad) * pathLenDeg / latScale;
            arrowHeading = headingDeg;
        }}

        var path = L.polyline([[lat, lng], [endLat, endLng]], {{
            renderer: canvasRenderer, color: '#ffd11a', weight: 2, dashArray: '4,8', opacity: 0.85, interactive: false
        }}).addTo(map);
        var arrowTip = L.marker([endLat, endLng], {{icon: arrowHeadIcon(arrowHeading), interactive: false}}).addTo(map);

        predictedPaths[trackKey] = {{ path: path, arrowTip: arrowTip }};
    }}
}}

function clearPath(trackKey) {{
    var state = predictedPaths[trackKey];
    if (state) {{
        map.removeLayer(state.path);
        map.removeLayer(state.arrowTip);
        delete predictedPaths[trackKey];
    }}
}}

function removeMarker(eventId) {{
    if (markers[eventId]) {{
        map.removeLayer(markers[eventId]);
        delete markers[eventId];
    }}
    delete markerMeta[eventId];
    clearPath(eventId);
}}

function clearMarkers() {{
    for (var id in markers) {{
        map.removeLayer(markers[id]);
    }}
    markers = {{}};
    markerMeta = {{}};
    for (var id in predictedPaths) {{
        clearPath(id);
    }}
    locationCounts = {{}};
}}

function focusMarker(eventId, zoom) {{
    if (markers[eventId]) {{
        // Pan to the marker always, but never zoom out to get there -- if the
        // operator is already zoomed in past the default focus level, respect
        // that instead of yanking them back out to it.
        var targetZoom = Math.max(map.getZoom(), zoom);
        map.setView(markers[eventId].getLatLng(), targetZoom);
    }}
}}

initMap();
</script>
</body>
</html>"""


class _Bridge(QObject):
    mapClicked = pyqtSignal(float, float)
    markerClicked = pyqtSignal(str)
    markerDoubleClicked = pyqtSignal(str)

    @pyqtSlot(float, float)
    def onMapClick(self, lat, lng):
        self.mapClicked.emit(lat, lng)

    @pyqtSlot(str)
    def onMarkerClick(self, event_id):
        self.markerClicked.emit(event_id)

    @pyqtSlot(str)
    def onMarkerDoubleClick(self, event_id):
        self.markerDoubleClicked.emit(event_id)


class _LoggingPage(QWebEnginePage):
    """Default QWebEnginePage swallows JS console output entirely -- a JS
    exception (e.g. inside a marker's click handler) fails completely
    silently, no different from working correctly. Surfacing it via a signal
    is what makes that kind of bug diagnosable at all.
    """
    consoleMessage = pyqtSignal(str)

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        self.consoleMessage.emit(f"{message} (line {line_number})")


class MapView(QWidget):
    mapClicked = pyqtSignal(float, float)
    eventClicked = pyqtSignal(str)         # single click -- focus the feed row
    eventDoubleClicked = pyqtSignal(str)   # double click -- open the media popup
    jsError = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._bridge = _Bridge()
        self._bridge.mapClicked.connect(self.mapClicked)
        self._bridge.markerClicked.connect(self.eventClicked)
        self._bridge.markerDoubleClicked.connect(self.eventDoubleClicked)

        self._web_view = QWebEngineView()
        self._page = _LoggingPage(self._web_view)
        self._page.consoleMessage.connect(self.jsError)
        self._web_view.setPage(self._page)
        self._channel = QWebChannel()
        self._channel.registerObject("pyHandler", self._bridge)
        self._page.setWebChannel(self._channel)

        self._loaded = False
        self._pending_js = []
        self._web_view.loadFinished.connect(self._on_load_finished)

        # Timed buffer: queued JS calls are dispatched _MAX_PER_FLUSH at a
        # time on a timer, not all at once. Under a fast-forwarded scenario,
        # events (and marker/path DOM churn) can arrive in bursts (e.g. 24
        # marker creations from a drone swarm landing in the same window) --
        # firing them all as one runJavaScript() call executes every one of
        # them synchronously in a row, a real hitch even though the *steady
        # state* with many objects already on the map is cheap (canvas
        # rendering). Same pattern as AgentManager's incident dispatch queue
        # (one at a time, gated by a timer) -- kept literally one-at-a-time
        # here too rather than a small batch, for consistency.
        self._js_queue = []
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(150)
        self._flush_timer.timeout.connect(self._flush_js_queue)
        self._flush_timer.start()

        with open(_GENERATED_HTML_PATH, "w") as f:
            f.write(_build_map_html())
        self._web_view.setUrl(QUrl.fromLocalFile(_GENERATED_HTML_PATH))

        layout.addWidget(self._web_view)

    def _on_load_finished(self, ok):
        self._loaded = ok
        if not ok:
            return
        for code in self._pending_js:
            self._web_view.page().runJavaScript(code)
        self._pending_js.clear()

    def _run_js(self, code: str):
        # Live events can arrive over ZMQ before Chromium finishes loading
        # the Leaflet page and running initMap() -- calling runJavaScript()
        # that early is a silent no-op (map is undefined), so queue until
        # loadFinished instead of dropping the marker.
        if self._loaded:
            self._js_queue.append(code)
        else:
            self._pending_js.append(code)

    _MAX_PER_FLUSH = 1

    def _flush_js_queue(self):
        if not self._js_queue:
            return
        chunk, self._js_queue = self._js_queue[: self._MAX_PER_FLUSH], self._js_queue[self._MAX_PER_FLUSH :]
        batch = ";\n".join(chunk)
        self._web_view.page().runJavaScript(batch)

    def add_event(self, event_id: str, lat: float, lon: float, level: int, event_type: str = None,
                  heading_deg: float = None, speed_kmh: float = None, track_id: str = None,
                  target_lat: float = None, target_lon: float = None):
        color = color_for_level(level)
        type_js = "''" if event_type is None else f"'{event_type}'"
        heading_js = "null" if heading_deg is None else heading_deg
        speed_js = "null" if speed_kmh is None else speed_kmh
        # track_id (tag_id) ties together repeat detections of the same
        # tracked object -- a fresh detection re-anchors that object's
        # predicted path to the new location instead of leaving a stale one.
        track_js = "null" if track_id is None else f"'{track_id}'"
        # target_lat/lon (if known): the path runs to this real destination
        # instead of a fixed-length line extrapolated from heading_deg alone.
        target_lat_js = "null" if target_lat is None else target_lat
        target_lon_js = "null" if target_lon is None else target_lon
        self._run_js(
            f"addOrUpdateMarker('{event_id}', {lat}, {lon}, '{color}', {type_js}, "
            f"{heading_js}, {speed_js}, {track_js}, {target_lat_js}, {target_lon_js})"
        )

    def remove_event(self, event_id: str):
        self._run_js(f"removeMarker('{event_id}')")

    def clear_events(self):
        self._run_js("clearMarkers()")

    def focus_event(self, event_id: str, zoom: int = 6):
        self._run_js(f"focusMarker('{event_id}', {zoom})")
