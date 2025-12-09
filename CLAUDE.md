# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web application for visualizing GPS sailing tracks from GPX files. It displays multiple sailing tracks on an interactive map with satellite imagery, topographic maps, and nautical chart overlays. Features include animated track playback with a boat icon, play/pause/reset controls, variable speed control, and a draggable control panel.

## Development Commands

### Running the Application
```bash
uv run python app.py
```
The app starts on `http://localhost:5000` with debug mode enabled.

### Dependency Management
```bash
# Sync dependencies from pyproject.toml
uv sync

# Add a new dependency
uv add package-name
```

## Architecture

### Core Components

**app.py** - Main Flask application containing all business logic:
- `TrackAnimation` (MacroElement): Custom Folium element that injects animation controls, CSS, and JavaScript directly into the map HTML (app.py:13-322)
- `parse_gpx_files()`: Scans directory for `.gpx` files, parses them with gpxpy, returns tracks and all coordinate points
- `calculate_bounds()`: Computes min/max/center lat/lon from all points for map framing
- `create_map()`: Builds Folium map with multiple tile layers, animated track visualization, and TrackAnimation element
- `index()`: Flask route that orchestrates parsing, bounds calculation, JSON serialization, and map rendering

**templates/index.html** - Jinja2 template that displays:
- Track metadata (filenames, point counts)
- Bounding box coordinates
- Embedded Folium map HTML (animation controls are injected into the map itself, not in this template)

### Map Visualization Details

The map uses **layered tile system** (app.py:59-111):
- Base layers: Esri Satellite, Esri Topo, OpenStreetMap, CartoDB Voyager (user-switchable)
- Overlay: OpenSeaMap nautical charts (toggleable)
- Layer control widget added via `folium.LayerControl()`

**Track rendering** (app.py:116-171):
- Each track gets two overlays: static polyline (60% opacity) + animated AntPath (moving dashes)
- Colors cycle through: blue, red, green, purple, orange, darkred, lightblue
- End markers: small red CircleMarker + permanent DivIcon label showing date extracted from filename
- Filename format expected: `YYYY-MM-DD.gpx` (label strips `.gpx` extension)

**Animation system** (app.py:22-321):
- Custom `TrackAnimation` MacroElement injects controls and JavaScript directly into Folium map HTML
- JavaScript-based playback with animated boat marker (⛵ emoji, 24px, auto-rotates based on bearing)
- Draggable control panel (bottom-right) with Play/Pause/Reset buttons and speed slider (0.5x-5x)
- Track selector dropdown allows animating individual tracks or all tracks concatenated
- Boat icon auto-rotates using bearing calculation between consecutive GPS points
- Track data passed as JSON via MacroElement initialization (app.py:201-204, 183)
- Controls run in same scope as map (solves iframe isolation issue)
- Drag functionality: click/drag panel header or empty space to reposition (buttons don't trigger drag)

### Data Flow

1. Flask app scans current directory for `*.gpx` files (app.py:330)
2. Each GPX file parsed into track segments → coordinate points (app.py:332-348)
3. All points aggregated to calculate map bounds (app.py:356-367)
4. Track data serialized to JSON for JavaScript animation (app.py:201-204)
5. Folium map created with center point, all tile layers, and tracks (app.py:54-180)
6. TrackAnimation MacroElement added to map with track JSON (app.py:183-184)
7. Map HTML generated via `_repr_html()` and injected into template via `map_html|safe` filter (index.html:92)

## Key Dependencies

- **Flask**: Web framework (routes, templating)
- **gpxpy**: GPX file parsing library
- **folium**: Python wrapper for Leaflet.js interactive maps
- **folium.plugins.AntPath**: Animated "marching ants" track visualization
- **folium.elements.MacroElement**: Base class for custom Folium elements (used for TrackAnimation)
- **jinja2.Template**: Template engine for MacroElement HTML/JavaScript injection

## File Organization

GPX files must be in the project root directory (same location as `app.py`) to be auto-discovered. The app expects filenames like `2025-10-11.gpx` where the date becomes the track label on the map.

## Configuration Points

- **Map tiles**: Modify tile layer URLs in `create_map()` (app.py:69-111)
- **Track styling**: Adjust PolyLine/AntPath parameters (app.py:120-137)
- **Animation controls position**: Change `bottom: 20px; right: 20px;` in TrackAnimation CSS (app.py:26-27)
- **Animation speed range**: Modify min/max/step in speed control input (app.py:97)
- **Boat icon size**: Change font-size in createBoatMarker() (app.py:130)
- **Server settings**: Change host/port in `app.run()` (app.py:215)
- **Track colors**: Edit colors list (app.py:114)

## Important Implementation Notes

- **Animation scope issue**: Animation controls and JavaScript must be injected into the Folium map HTML (via MacroElement) to share scope with the map object. External JavaScript in the template cannot access the map due to iframe isolation.
- **Drag behavior**: Dragging is disabled on interactive elements (buttons, inputs, select) to prevent conflicts with control interactions. Only header and empty space trigger drag.
- **Browser warnings**: "Tracking Prevention" warnings for CDN resources (jsdelivr, cloudflare) are normal browser privacy features and do not affect functionality.
