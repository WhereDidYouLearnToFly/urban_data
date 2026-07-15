"""Map view — right column. Interactive Leaflet map (Canada + Arctic) embedded
via QWebEngineView + QWebChannel, ported from the github/qtmap example
(radiolab9, MIT). Event dots are plotted at their coordinates and colored by
severity; clicking a dot is meant to focus the Agents panel / feed on that
incident (Step 4 wiring, not yet connected — this widget only emits the
signal).

Bundled assets live in ui/map_assets/ (Leaflet 1.9.4 + Canada province
outline). Tiles are fetched live from CartoDB's CDN — this needs internet at
demo time; the qtmap example's offline tile-server story (see its README)
was never actually wired up in that repo, so it wasn't ported here.
"""
import os

from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
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
var markers = {{}};
var pyHandler = null;

new QWebChannel(qt.webChannelTransport, function(channel) {{
    pyHandler = channel.objects.pyHandler;
}});

function initMap() {{
    map = L.map('map', {{
        zoomControl: true,
        crs: L.CRS.EPSG3857
    }}).setView([62.0, -98.0], 3);

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
}}

function addOrUpdateMarker(eventId, lat, lng, label, color) {{
    if (markers[eventId]) {{
        map.removeLayer(markers[eventId]);
    }}
    var icon = L.divIcon({{
        className: 'event-marker',
        html: '<div style="background:' + color + ';width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 0 4px rgba(0,0,0,0.6);"></div>',
        iconSize: [18, 18],
        iconAnchor: [9, 9]
    }});
    var marker = L.marker([lat, lng], {{icon: icon}}).addTo(map);
    marker.bindPopup('<b>' + label + '</b>');
    marker.on('click', function() {{
        if (pyHandler) {{
            pyHandler.onMarkerClick(eventId);
        }}
    }});
    markers[eventId] = marker;
}}

function removeMarker(eventId) {{
    if (markers[eventId]) {{
        map.removeLayer(markers[eventId]);
        delete markers[eventId];
    }}
}}

function clearMarkers() {{
    for (var id in markers) {{
        map.removeLayer(markers[id]);
    }}
    markers = {{}};
}}

function focusMarker(eventId, zoom) {{
    if (markers[eventId]) {{
        map.setView(markers[eventId].getLatLng(), zoom);
    }}
}}

initMap();
</script>
</body>
</html>"""


class _Bridge(QObject):
    mapClicked = pyqtSignal(float, float)
    markerClicked = pyqtSignal(str)

    @pyqtSlot(float, float)
    def onMapClick(self, lat, lng):
        self.mapClicked.emit(lat, lng)

    @pyqtSlot(str)
    def onMarkerClick(self, event_id):
        self.markerClicked.emit(event_id)


class MapView(QWidget):
    mapClicked = pyqtSignal(float, float)
    eventClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._bridge = _Bridge()
        self._bridge.mapClicked.connect(self.mapClicked)
        self._bridge.markerClicked.connect(self.eventClicked)

        self._web_view = QWebEngineView()
        self._channel = QWebChannel()
        self._channel.registerObject("pyHandler", self._bridge)
        self._web_view.page().setWebChannel(self._channel)
        self._web_view.loadFinished.connect(self._on_load_finished)

        with open(_GENERATED_HTML_PATH, "w") as f:
            f.write(_build_map_html())
        self._web_view.setUrl(QUrl.fromLocalFile(_GENERATED_HTML_PATH))

        layout.addWidget(self._web_view)

    def _on_load_finished(self, ok):
        if ok:
            self._add_placeholder_events()

    def _run_js(self, code: str):
        self._web_view.page().runJavaScript(code)

    def add_event(self, event_id: str, lat: float, lon: float, level: int, description: str):
        color = color_for_level(level)
        label = description.replace("\\", "\\\\").replace("'", "\\'")
        self._run_js(f"addOrUpdateMarker('{event_id}', {lat}, {lon}, '{label}', '{color}')")

    def remove_event(self, event_id: str):
        self._run_js(f"removeMarker('{event_id}')")

    def clear_events(self):
        self._run_js("clearMarkers()")

    def focus_event(self, event_id: str, zoom: int = 8):
        self._run_js(f"focusMarker('{event_id}', {zoom})")

    def _add_placeholder_events(self):
        for event_id, level, description, (lat, lon) in [
            ("ph-1", 1, "Traffic normal — Hwy 401 westbound", (43.70, -79.55)),
            ("ph-2", 5, "Ambulance dispatched — Ottawa downtown", (45.4215, -75.6972)),
            ("ph-3", 8, "Flood warning — Don River rising", (43.6629, -79.3568)),
            ("ph-4", 1, "Nothing to report — Vancouver harbour", (49.2827, -123.1207)),
        ]:
            self.add_event(event_id, lat, lon, level, description)
