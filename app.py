import os
import glob
import gpxpy
import folium
from folium import plugins
from folium.elements import Element, MacroElement
from jinja2 import Template
from flask import Flask, render_template
import json

app = Flask(__name__)

class TrackAnimation(MacroElement):
    """Adds track animation functionality to a Folium map."""

    def __init__(self, tracks_data):
        super(TrackAnimation, self).__init__()
        self._name = 'TrackAnimation'
        self.tracks_data = tracks_data

        self._template = Template("""
        {% macro html(this, kwargs) %}
        <style>
            .animation-controls {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                z-index: 1000;
                min-width: 200px;
                cursor: move;
            }
            .animation-controls h4 {
                margin: 0 0 10px 0;
                color: #333;
                font-size: 14px;
            }
            .control-group {
                margin-bottom: 10px;
            }
            .control-group label {
                display: block;
                font-size: 12px;
                color: #666;
                margin-bottom: 4px;
            }
            .control-group select,
            .control-group input {
                width: 100%;
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            .btn {
                width: 100%;
                padding: 8px;
                margin: 4px 0;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            }
            .btn-primary {
                background-color: #4CAF50;
                color: white;
            }
            .btn-primary:hover {
                background-color: #45a049;
            }
            .btn-secondary {
                background-color: #f44336;
                color: white;
            }
            .btn-secondary:hover {
                background-color: #da190b;
            }
            .btn:disabled {
                background-color: #cccccc;
                cursor: not-allowed;
            }
        </style>
        <div class="animation-controls">
            <h4>Track Animation</h4>
            <div class="control-group">
                <label for="track-select">Select Track:</label>
                <select id="track-select">
                    <option value="all">All Tracks</option>
                </select>
            </div>
            <div class="control-group">
                <label for="speed-control">Speed: <span id="speed-value">1x</span></label>
                <input type="range" id="speed-control" min="0.5" max="5" step="0.5" value="1">
            </div>
            <button id="play-btn" class="btn btn-primary">Play</button>
            <button id="pause-btn" class="btn btn-secondary" disabled>Pause</button>
            <button id="reset-btn" class="btn">Reset</button>
        </div>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function() {
            var tracksData = {{ this.tracks_data|safe }};
            var map = {{ this._parent.get_name() }};

            // Populate track selector
            var trackSelect = document.getElementById('track-select');
            tracksData.forEach(function(track, index) {
                var option = document.createElement('option');
                option.value = index;
                option.textContent = track.name;
                trackSelect.appendChild(option);
            });

            // Animation state
            var animationMarker = null;
            var currentPointIndex = 0;
            var animationInterval = null;
            var animationSpeed = 1;
            var isAnimating = false;

            // Create boat marker
            function createBoatMarker() {
                var boatIcon = L.divIcon({
                    className: 'boat-marker',
                    html: '<div style="font-size: 24px; transform: rotate(0deg);">⛵</div>',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });

                animationMarker = L.marker([0, 0], {
                    icon: boatIcon,
                    zIndexOffset: 1000
                });
            }

            // Get current track based on selection
            function getCurrentTrack() {
                var trackSelect = document.getElementById('track-select');
                if (!trackSelect) return tracksData[0].points;

                var selectedValue = trackSelect.value;
                if (selectedValue === 'all') {
                    var allPoints = [];
                    tracksData.forEach(function(track) {
                        allPoints = allPoints.concat(track.points);
                    });
                    return allPoints;
                } else {
                    var trackIndex = parseInt(selectedValue);
                    return tracksData[trackIndex].points;
                }
            }

            // Calculate bearing
            function calculateBearing(lat1, lon1, lat2, lon2) {
                var dLon = (lon2 - lon1) * Math.PI / 180;
                var y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
                var x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
                        Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
                var bearing = Math.atan2(y, x) * 180 / Math.PI;
                return (bearing + 360) % 360;
            }

            // Start animation
            function startAnimation() {
                console.log('Starting animation');

                if (!animationMarker) {
                    createBoatMarker();
                }

                var track = getCurrentTrack();
                if (!track || track.length === 0) {
                    console.error('No track data');
                    return;
                }

                if (!map.hasLayer(animationMarker)) {
                    animationMarker.addTo(map);
                }

                if (currentPointIndex >= track.length) {
                    currentPointIndex = 0;
                }

                isAnimating = true;
                updateButtons();

                var baseInterval = 50;
                var interval = baseInterval / animationSpeed;

                animationInterval = setInterval(function() {
                    if (currentPointIndex >= track.length) {
                        stopAnimation();
                        return;
                    }

                    var point = track[currentPointIndex];
                    animationMarker.setLatLng(point);

                    if (currentPointIndex < track.length - 1) {
                        var nextPoint = track[currentPointIndex + 1];
                        var angle = calculateBearing(point[0], point[1], nextPoint[0], nextPoint[1]);
                        var iconHtml = '<div style="font-size: 24px; transform: rotate(' + angle + 'deg);">⛵</div>';
                        animationMarker.setIcon(L.divIcon({
                            className: 'boat-marker',
                            html: iconHtml,
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        }));
                    }

                    currentPointIndex++;
                }, interval);
            }

            // Pause animation
            function pauseAnimation() {
                if (animationInterval) {
                    clearInterval(animationInterval);
                    animationInterval = null;
                }
                isAnimating = false;
                updateButtons();
            }

            // Stop animation
            function stopAnimation() {
                pauseAnimation();
                currentPointIndex = 0;
                if (map.hasLayer(animationMarker)) {
                    map.removeLayer(animationMarker);
                }
                updateButtons();
            }

            // Update buttons
            function updateButtons() {
                var playBtn = document.getElementById('play-btn');
                var pauseBtn = document.getElementById('pause-btn');
                if (playBtn) playBtn.disabled = isAnimating;
                if (pauseBtn) pauseBtn.disabled = !isAnimating;
            }

            // Event listeners
            window.addEventListener('load', function() {
                var playBtn = document.getElementById('play-btn');
                var pauseBtn = document.getElementById('pause-btn');
                var resetBtn = document.getElementById('reset-btn');
                var speedControl = document.getElementById('speed-control');
                var trackSelect = document.getElementById('track-select');

                if (playBtn) {
                    playBtn.addEventListener('click', startAnimation);
                }
                if (pauseBtn) {
                    pauseBtn.addEventListener('click', pauseAnimation);
                }
                if (resetBtn) {
                    resetBtn.addEventListener('click', stopAnimation);
                }
                if (speedControl) {
                    speedControl.addEventListener('input', function(e) {
                        animationSpeed = parseFloat(e.target.value);
                        document.getElementById('speed-value').textContent = animationSpeed + 'x';
                        if (isAnimating) {
                            pauseAnimation();
                            startAnimation();
                        }
                    });
                }
                if (trackSelect) {
                    trackSelect.addEventListener('change', stopAnimation);
                }

                console.log('Animation ready');
            });

            // Make controls draggable
            var controls = document.querySelector('.animation-controls');
            var isDragging = false;
            var currentX;
            var currentY;
            var initialX;
            var initialY;
            var xOffset = 0;
            var yOffset = 0;

            controls.addEventListener('mousedown', function(e) {
                // Don't drag if clicking on buttons or inputs
                if (e.target.tagName === 'BUTTON' || e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
                    return;
                }

                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
                isDragging = true;
            });

            document.addEventListener('mousemove', function(e) {
                if (isDragging) {
                    e.preventDefault();
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                    xOffset = currentX;
                    yOffset = currentY;

                    controls.style.transform = 'translate(' + currentX + 'px, ' + currentY + 'px)';
                }
            });

            document.addEventListener('mouseup', function() {
                isDragging = false;
            });
        })();
        {% endmacro %}
        """)

def parse_gpx_files(gpx_directory="."):
    """Parse all GPX files in the directory and extract track points."""
    all_points = []
    tracks = []

    # Find all GPX files
    gpx_files = glob.glob(os.path.join(gpx_directory, "*.gpx"))

    for gpx_file in sorted(gpx_files):
        with open(gpx_file, 'r') as f:
            gpx = gpxpy.parse(f)

            track_points = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        track_points.append((point.latitude, point.longitude))
                        all_points.append((point.latitude, point.longitude))

            if track_points:
                tracks.append({
                    'name': os.path.basename(gpx_file),
                    'points': track_points
                })

    return tracks, all_points

def calculate_bounds(points):
    """Calculate the bounding box for all points."""
    if not points:
        return None

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons),
        'center_lat': (min(lats) + max(lats)) / 2,
        'center_lon': (min(lons) + max(lons)) / 2
    }

def create_map(tracks, bounds, tracks_json):
    """Create a Folium map with all tracks."""
    if not bounds:
        return None

    # Create map centered on the data - start with no default tiles
    m = folium.Map(
        location=[bounds['center_lat'], bounds['center_lon']],
        zoom_start=14,
        tiles=None,
        control_scale=True
    )

    # Add multiple detailed base map options
    # Esri World Imagery (Satellite with high detail)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite Imagery',
        overlay=False,
        control=True
    ).add_to(m)

    # Esri World Topo Map (detailed topographic)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Detailed Topo Map',
        overlay=False,
        control=True
    ).add_to(m)

    # OpenStreetMap (standard)
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    ).add_to(m)

    # CartoDB Voyager (detailed street map with terrain)
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name='CartoDB Voyager',
        overlay=False,
        control=True
    ).add_to(m)

    # Add OpenSeaMap nautical chart overlay
    folium.TileLayer(
        tiles='https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png',
        attr='Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors',
        name='Nautical Charts',
        overlay=True,
        control=True,
        opacity=0.85
    ).add_to(m)

    # Add each track to the map with a different color
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 'lightblue']

    for idx, track in enumerate(tracks):
        color = colors[idx % len(colors)]

        # Add static polyline
        folium.PolyLine(
            track['points'],
            color=color,
            weight=3,
            opacity=0.6,
            popup=track['name']
        ).add_to(m)

        # Add animated "ant path" overlay
        plugins.AntPath(
            track['points'],
            color=color,
            weight=4,
            opacity=0.8,
            delay=800,
            dash_array=[10, 20],
            pulse_color='white'
        ).add_to(m)

        # Add end marker with permanent date label
        if track['points']:
            # Extract date from filename (e.g., "2025-10-11.gpx" -> "2025-10-11")
            filename = track['name']
            date_label = filename.replace('.gpx', '')

            # End marker - small red circle
            folium.CircleMarker(
                track['points'][-1],
                radius=6,
                color='darkred',
                fill=True,
                fillColor='red',
                fillOpacity=0.9,
                weight=2,
                popup=f"End: {track['name']}"
            ).add_to(m)

            # Permanent date label
            folium.Marker(
                track['points'][-1],
                icon=folium.DivIcon(html=f'''
                    <div style="
                        font-size: 11px;
                        font-weight: bold;
                        color: #b71c1c;
                        text-shadow: -1px -1px 0 white, 1px -1px 0 white, -1px 1px 0 white, 1px 1px 0 white;
                        white-space: nowrap;
                        margin-left: 8px;
                        margin-top: -6px;
                    ">{date_label}</div>
                ''')
            ).add_to(m)

    # Add layer control to toggle nautical charts
    folium.LayerControl().add_to(m)

    # Fit bounds to show all tracks
    m.fit_bounds([
        [bounds['min_lat'], bounds['min_lon']],
        [bounds['max_lat'], bounds['max_lon']]
    ])

    # Add animation functionality
    animation = TrackAnimation(tracks_json)
    animation.add_to(m)

    return m

@app.route('/')
def index():
    """Main route to display the map."""
    # Parse GPX files
    tracks, all_points = parse_gpx_files()

    if not tracks:
        return render_template('index.html', error="No GPX files found in the directory.")

    # Calculate bounds
    bounds = calculate_bounds(all_points)

    # Prepare track data for JavaScript animation
    tracks_json = json.dumps([{
        'name': track['name'],
        'points': [[lat, lon] for lat, lon in track['points']]
    } for track in tracks])

    # Create map with animation
    map_obj = create_map(tracks, bounds, tracks_json)

    # Convert map to HTML
    map_html = map_obj._repr_html_()

    return render_template('index.html', map_html=map_html, tracks=tracks, bounds=bounds)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
