# GPX Sailing Track Viewer - Technical Specification

## Overview

A Flask web application for visualizing GPS sailing tracks from GPX files with interactive mapping, animated playback, and multiple map layer options including nautical charts.

## Core Functionality

### 1. GPX File Processing
- Automatically discovers and parses all `.gpx` files in the project root directory
- Supports multiple GPX files simultaneously
- Extracts track segments and coordinate points (latitude/longitude)
- Calculates bounding box (min/max coordinates) for automatic map framing
- Expected filename format: `YYYY-MM-DD.gpx` (date extracted for track labeling)

### 2. Interactive Map Visualization

#### Base Map Layers (User-Switchable)
- **Esri World Imagery**: High-detail satellite imagery
- **Esri World Topo Map**: Detailed topographic map
- **OpenStreetMap**: Standard street map
- **CartoDB Voyager**: Detailed street map with terrain features

#### Overlay Layer
- **OpenSeaMap**: Nautical chart overlay (toggleable, 85% opacity)
- Layer control widget in upper-right corner for switching between layers

#### Track Rendering
Each track is rendered with dual visualization:
- **Static polyline**: 60% opacity, 3px weight, colored uniquely per track
- **Animated AntPath**: Moving "marching ants" effect (80% opacity, 4px weight, 800ms delay)
- **Color palette**: blue, red, green, purple, orange, darkred, lightblue (cycles)

#### Track Markers
- **End markers**: Small red CircleMarker (6px radius) at track endpoint
- **Date labels**: Permanent DivIcon showing filename without extension, positioned at track end
- Label styling: 11px bold text, dark red (#b71c1c), white text shadow for visibility

### 3. Track Animation System

#### Animated Boat Icon
- **Icon**: Sailboat emoji (⛵) displayed at 24px size
- **Behavior**: Moves along GPS track points from start to finish
- **Auto-rotation**: Calculates bearing between consecutive points to face direction of travel
- **Z-index**: 1000 (appears above all map elements)

#### Animation Controls (Draggable Panel)
**Position**: Lower-right corner by default, fully draggable

**Controls**:
- **Track Selector**: Dropdown to choose individual track or "All Tracks" (concatenated)
- **Speed Control**: Slider from 0.5x to 5x speed (default: 1x, 50ms base interval)
- **Play Button**: Start/resume animation (disabled while animating)
- **Pause Button**: Pause animation at current position (disabled when stopped)
- **Reset Button**: Stop animation, remove boat icon, reset to start

**Panel Styling**:
- White background, 15px padding, 8px border radius
- 2px shadow for depth
- 200px minimum width
- Cursor changes to "move" on hover

**Drag Functionality**:
- Click and drag panel header or empty space to reposition
- Clicking buttons/inputs/select elements does not trigger drag
- Position persists during session

### 4. User Interface

#### Main Page Layout
- **Header**: "GPX Sailing Track Viewer" title
- **Track Information Panel**:
  - List of loaded tracks with filename and point count
  - Bounding box coordinates (North/South/East/West in degrees, 6 decimal places)
- **Map Container**: 600px height, full width, embedded Folium map with iframe

#### Styling
- Clean, modern interface with light gray background (#f5f5f5)
- White container with subtle shadow
- Info panels with light blue background (#e8f4f8)
- Responsive layout (max-width: 1400px, centered)

### 5. Technical Architecture

#### Backend (Flask)
**Main Functions**:
- `parse_gpx_files()`: Scans directory, parses GPX files with gpxpy library
- `calculate_bounds()`: Computes min/max/center coordinates for map framing
- `create_map()`: Builds Folium map with layers, tracks, and animation element
- `index()`: Flask route orchestrating data flow and template rendering

**Custom Folium Element**:
- `TrackAnimation` MacroElement: Injects HTML, CSS, and JavaScript into map
- Contains complete animation logic within map scope (solves iframe isolation issue)
- Uses Jinja2 templating to reference map variable name dynamically

#### Frontend (JavaScript)
**Animation Engine** (injected into Folium map):
- Track data passed as JSON from Flask
- Interval-based animation loop (50ms base / speed multiplier)
- Leaflet DivIcon with dynamic HTML for rotation
- Bearing calculation using Haversine formula
- Event listeners for all control interactions

**Drag System**:
- Mouse event handlers (mousedown, mousemove, mouseup)
- Transform-based positioning (translate CSS)
- Offset tracking for smooth dragging

#### Dependencies (pyproject.toml)
- **flask** (>=3.1.2): Web framework
- **folium** (>=0.20.0): Interactive map generation, Leaflet.js wrapper
- **gpxpy** (>=1.6.2): GPX file parsing
- **Python**: >=3.12
- **Package manager**: uv (modern Python package installer)

### 6. Data Flow

1. Flask app scans project directory for `*.gpx` files
2. Each GPX file parsed into track segments with coordinate points
3. All points aggregated to calculate map bounds (min/max lat/lon, center)
4. Track data serialized to JSON for JavaScript consumption
5. Folium map created with center point, zoom level, tile layers
6. Tracks rendered as PolyLine + AntPath + end markers + labels
7. TrackAnimation MacroElement added to map with track JSON
8. Map HTML generated and injected into template via `map_html|safe`
9. Template renders with track metadata, bounding box info, and embedded map

### 7. File Organization

```
project-root/
├── app.py                    # Main Flask application
├── templates/
│   └── index.html           # Jinja2 template for map display
├── *.gpx                    # GPX track files (auto-discovered)
├── pyproject.toml           # uv dependency configuration
├── CLAUDE.md                # Development guidance for Claude Code
├── SPECIFICATION.md         # This file
└── README.md                # User-facing documentation
```

**Important**: GPX files must be in project root directory (same location as `app.py`)

## Development Workflow

### Running the Application
```bash
uv run python app.py
```
- Starts on `http://localhost:5000` (all interfaces: 0.0.0.0)
- Debug mode enabled (auto-reloads on code changes)
- Accessible on local network via machine IP address

### Dependency Management
```bash
# Sync dependencies from pyproject.toml
uv sync

# Add new dependency
uv add package-name
```

### Adding New GPX Files
1. Place GPX file in project root directory
2. Use format `YYYY-MM-DD.gpx` for automatic date labeling
3. Refresh browser - file will be auto-discovered and displayed

## Configuration Options

### Map Tiles
Modify tile layer URLs in `create_map()` function (app.py:69-111)

### Track Styling
Adjust PolyLine/AntPath parameters:
- Line weight, opacity, color (app.py:120-137)
- AntPath delay, dash array (app.py:129-137)

### Animation Settings
Modify animation parameters:
- Base interval speed (app.py:194): default 50ms
- Speed range (app.py:96-97): default 0.5x-5x
- Boat icon size (app.py:130): default 24px

### Track Colors
Edit colors list (app.py:114): currently 7 colors cycling

### Server Settings
Change host/port in `app.run()` (app.py:215):
- Default: `host='0.0.0.0', port=5000, debug=True`

## Known Behaviors

### Browser Tracking Prevention
- Modern browsers (Edge, Safari) may show "Tracking Prevention" warnings for CDN resources
- These are harmless warnings - resources still load and function correctly
- CDNs blocked from localStorage access only (privacy feature)
- Does not affect map or animation functionality

### Animation Scope
- Animation controls and JavaScript run inside Folium map iframe
- Controls injected into map HTML to share scope with map object
- Solves cross-origin and iframe isolation issues

### Drag Behavior
- Dragging only works on panel header or empty space
- Interactive elements (buttons, slider, dropdown) do not trigger drag
- Panel position resets on page refresh

## Future Enhancement Ideas

- Persist dragged panel position in localStorage
- Add animation progress bar
- Display current speed/distance metrics during playback
- Support for track editing/trimming
- Export animated track as video/GIF
- Multi-track synchronized playback
- Waypoint markers and labels
- Track statistics (distance, duration, average speed)
- Track comparison overlay
