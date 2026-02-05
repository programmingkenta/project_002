"""
Build Isometric Shibuya Crossing from OpenStreetMap data.

This script:
1. Parses an .osm file (XML) for building data
2. Extracts building footprints, heights, and names
3. Generates an interactive isometric HTML map

This is the SAME pipeline used by Isometric NYC:
  Real data → Parse → Transform → Render isometrically
"""

import xml.etree.ElementTree as ET
import math
import json

# === STEP 1: PARSE THE OSM FILE ===
print("Step 1: Parsing OSM file...")

osm_file = "/home/kenta/Downloads/Shibuya Crossing Map.osm"
tree = ET.parse(osm_file)
root = tree.getroot()

# Build a lookup of all nodes: node_id -> (lat, lon)
# This is like building a dictionary — same as your city builder!
nodes = {}
for node in root.findall("node"):
    node_id = node.get("id")
    lat = float(node.get("lat"))
    lon = float(node.get("lon"))
    nodes[node_id] = {"lat": lat, "lon": lon}

print(f"  Found {len(nodes)} nodes (map points)")

# === STEP 2: EXTRACT BUILDINGS ===
print("Step 2: Extracting buildings...")

buildings = []

for way in root.findall("way"):
    tags = {}
    for tag in way.findall("tag"):
        tags[tag.get("k")] = tag.get("v")

    # Skip if not a building
    if "building" not in tags:
        continue

    # Get the node references (the building's outline)
    node_refs = [nd.get("ref") for nd in way.findall("nd")]

    # Convert node refs to actual coordinates
    coords = []
    for ref in node_refs:
        if ref in nodes:
            coords.append(nodes[ref])

    if len(coords) < 3:
        continue  # Need at least 3 points for a polygon

    # Extract building properties
    name = tags.get("name:en") or tags.get("name") or ""
    levels = int(tags.get("building:levels", 2))
    building_type = tags.get("building", "yes")

    # Calculate center point of the building
    center_lat = sum(c["lat"] for c in coords) / len(coords)
    center_lon = sum(c["lon"] for c in coords) / len(coords)

    buildings.append({
        "name": name,
        "levels": levels,
        "type": building_type,
        "center_lat": center_lat,
        "center_lon": center_lon,
        "coords": coords,
    })

print(f"  Found {len(buildings)} buildings (OSM)")

# Show some named buildings
named = [b for b in buildings if b["name"]]
print(f"  Named buildings: {len(named)}")
for b in named:
    print(f"    - {b['name']} ({b['levels']} levels)")

# === STEP 2A: LOAD PLATEAU BUILDING DATA ===
# PLATEAU has real surveyed heights and footprints — much more accurate than OSM!
print("Step 2a: Loading PLATEAU building data...")

import os
plateau_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "plateau_data", "shibuya_crossing_buildings.json")

if os.path.exists(plateau_path):
    with open(plateau_path) as f:
        plateau_buildings = json.load(f)

    print(f"  Loaded {len(plateau_buildings)} PLATEAU buildings")

    # Build OSM name lookup: match PLATEAU buildings to nearby OSM named buildings
    # This lets us keep OSM street names while using PLATEAU geometry
    osm_named = {b["name"]: b for b in buildings if b["name"]}

    # Convert PLATEAU format to our pipeline format
    # PLATEAU gives us: real height, real floors, real footprint, usage type
    USAGE_MAP = {
        "401": "office", "402": "shop", "403": "hotel", "404": "commercial",
        "411": "house", "412": "apartment", "413": "shop_house", "414": "shop_apartment",
        "415": "workshop_house", "421": "government", "422": "school",
        "431": "transport", "441": "factory", "461": "unknown",
    }

    buildings = []  # Replace OSM buildings with PLATEAU data!

    for pb in plateau_buildings:
        if "footprint" not in pb or "height" not in pb:
            continue
        if pb["height"] <= 0 or pb["height"] > 500:
            continue

        # Convert footprint [(lat,lon), ...] to coord dicts
        coords = [{"lat": pt[0], "lon": pt[1]} for pt in pb["footprint"]]
        if len(coords) < 3:
            continue

        center_lat = pb.get("center_lat", sum(c["lat"] for c in coords) / len(coords))
        center_lon = pb.get("center_lon", sum(c["lon"] for c in coords) / len(coords))

        usage_code = pb.get("usage_code", "461")
        usage = USAGE_MAP.get(usage_code, "unknown")
        floors = pb.get("floors", max(1, int(pb["height"] / 3.5)))
        if floors >= 9999:
            floors = max(1, int(pb["height"] / 3.5))

        buildings.append({
            "name": "",  # PLATEAU doesn't include names
            "levels": floors,
            "type": usage,
            "height_m": pb["height"],  # Real surveyed height!
            "center_lat": center_lat,
            "center_lon": center_lon,
            "coords": coords,
        })

    # Try to match OSM names to nearest PLATEAU building
    for osm_b in named:
        best_dist = 999999
        best_match = None
        for pb in buildings:
            dlat = (osm_b["center_lat"] - pb["center_lat"]) * 111000
            dlon = (osm_b["center_lon"] - pb["center_lon"]) * 91000
            dist = math.sqrt(dlat**2 + dlon**2)
            if dist < best_dist:
                best_dist = dist
                best_match = pb
        if best_match and best_dist < 30:  # Within 30 meters
            best_match["name"] = osm_b["name"]

    # === HERO BUILDINGS: Shibuya's iconic landmarks ===
    # Each hero building gets billboards and special rendering
    HERO_BUILDINGS = {
        "Q-FRONT": {
            "billboards": [
                {"u0": 0.05, "v0": 0.20, "u1": 0.95, "v1": 0.75, "color": "#FF2255"},
            ],
            "accent": "#00704A",
            "rooftop": "billboard_top",
        },
        "MAGNET SHIBUYA": {
            "billboards": [
                {"u0": 0.10, "v0": 0.15, "u1": 0.90, "v1": 0.80, "color": "#3366FF"},
            ],
            "accent": "#3366FF",
            "rooftop": "screen",
        },
        "Shibuya Scramble Square": {
            "billboards": [],
            "accent": "#CCDDEE",
            "rooftop": "antenna",
        },
        "Seibu Shibuya Department Store A Building": {
            "billboards": [
                {"u0": 0.10, "v0": 0.30, "u1": 0.60, "v1": 0.70, "color": "#EE4444"},
            ],
            "accent": "#CC2222",
            "rooftop": "sign",
        },
        "Shibuya Mark City East": {
            "billboards": [
                {"u0": 0.15, "v0": 0.25, "u1": 0.55, "v1": 0.65, "color": "#FF8844"},
            ],
            "accent": "#886644",
            "rooftop": "helipad",
        },
        "Shibuya Toei Plaza": {
            "billboards": [
                {"u0": 0.10, "v0": 0.25, "u1": 0.70, "v1": 0.65, "color": "#FFAA00"},
            ],
            "accent": "#FFAA00",
            "rooftop": "antenna",
        },
    }

    # Tag hero buildings
    for b in buildings:
        if b["name"] in HERO_BUILDINGS:
            b["hero"] = HERO_BUILDINGS[b["name"]]

    print(f"  Using {len(buildings)} PLATEAU buildings (real heights!)")
    named = [b for b in buildings if b["name"]]
    print(f"  Matched {len(named)} building names from OSM")
    for b in named:
        hero_tag = " [HERO]" if "hero" in b else ""
        print(f"    - {b['name']} ({b['height_m']:.0f}m, {b['levels']}F, {b['type']}){hero_tag}")
else:
    print("  PLATEAU data not found, using OSM buildings only")
    for b in buildings:
        b["height_m"] = b["levels"] * 3.5
        b["type"] = "unknown"

# === STEP 2B: EXTRACT ROADS ===
print("Step 2b: Extracting roads and paths...")

roads = []

for way in root.findall("way"):
    tags = {}
    for tag in way.findall("tag"):
        tags[tag.get("k")] = tag.get("v")

    # Look for highway tags (roads, paths, crossings)
    highway_type = tags.get("highway")
    if not highway_type:
        continue

    # Skip non-road types
    if highway_type in ("bus_stop", "traffic_signals", "crossing"):
        continue

    node_refs = [nd.get("ref") for nd in way.findall("nd")]
    coords = []
    for ref in node_refs:
        if ref in nodes:
            coords.append(nodes[ref])

    if len(coords) < 2:
        continue

    name = tags.get("name:en") or tags.get("name") or ""
    lanes = int(tags.get("lanes", 2))

    # Determine road width based on type
    if highway_type in ("primary", "trunk"):
        width = 12
    elif highway_type in ("secondary", "tertiary"):
        width = 8
    elif highway_type == "pedestrian":
        width = 6
    elif highway_type == "footway":
        width = 3
    elif highway_type == "service":
        width = 4
    else:
        width = 5

    roads.append({
        "name": name,
        "type": highway_type,
        "width": width,
        "coords": coords,
    })

print(f"  Found {len(roads)} roads/paths")
for r in roads:
    if r["name"]:
        print(f"    - {r['name']} ({r['type']})")

# === STEP 2C: EXTRACT SCRAMBLE CROSSING ===
print("Step 2c: Extracting scramble crossing...")

scramble_area = None
scramble_crossings = []

for way in root.findall("way"):
    tags = {}
    for tag in way.findall("tag"):
        tags[tag.get("k")] = tag.get("v")

    is_scramble = tags.get("crossing:scramble") == "yes"
    is_area = tags.get("area") == "yes"
    alt_name = tags.get("alt_name:en", "")

    # The scramble crossing area polygon
    if "Scramble Crossing" in alt_name or (is_area and "junction" in tags):
        node_refs = [nd.get("ref") for nd in way.findall("nd")]
        coords = [nodes[ref] for ref in node_refs if ref in nodes]
        if len(coords) >= 3:
            scramble_area = coords
            print(f"  Found scramble crossing area with {len(coords)} points")

    # Individual crossing lines (the zebra paths)
    if is_scramble and tags.get("highway") == "footway":
        node_refs = [nd.get("ref") for nd in way.findall("nd")]
        coords = [nodes[ref] for ref in node_refs if ref in nodes]
        if len(coords) >= 2:
            scramble_crossings.append(coords)

print(f"  Found {len(scramble_crossings)} crossing paths")

# === STEP 2D: LOAD RAILWAY & STATION DATA ===
# Real railway lines from PLATEAU/GSI GeoJSON — same data Tokyo Metro uses!
print("Step 2d: Loading railway and station data...")

data_dir = os.path.dirname(os.path.abspath(__file__))
railway_path = os.path.join(data_dir, "plateau_data", "shibuya_related",
                            "13113_shibuya-ku_pref_2023_railway.geojson")
station_path = os.path.join(data_dir, "plateau_data", "shibuya_related",
                            "13113_shibuya-ku_pref_2023_station.geojson")

# Official Tokyo railway line colors (the real ones from station maps!)
LINE_COLORS = {
    "山手線":         "#80C241",  # JR Yamanote — the famous green loop
    "中央線":         "#F15A22",  # JR Chuo — orange
    "井の頭線":       "#9B7CB6",  # Keio Inokashira — lavender
    "京王線":         "#DD0033",  # Keio — crimson
    "小田原線":       "#1E72B7",  # Odakyu — blue
    "田園都市線":     "#009944",  # Tokyu Den-en-toshi — green
    "東横線":         "#E5171F",  # Tokyu Toyoko — red
    "3号線銀座線":    "#F39700",  # Tokyo Metro Ginza — orange
    "11号線半蔵門線": "#8F76D6",  # Tokyo Metro Hanzomon — purple
    "13号線副都心線": "#9C5E31",  # Tokyo Metro Fukutoshin — brown
    "9号線千代田線":  "#00A650",  # Tokyo Metro Chiyoda — green
    "2号線日比谷線":  "#B5B5AC",  # Tokyo Metro Hibiya — silver
    "10号線新宿線":   "#6CBB5A",  # Toei Shinjuku — leaf green
    "12号線大江戸線": "#B6007A",  # Toei Oedo — magenta
}

railways = []
stations = []

if os.path.exists(railway_path):
    with open(railway_path) as f:
        railway_geojson = json.load(f)

    # Each feature is a segment of a railway line (MultiLineString)
    for feature in railway_geojson["features"]:
        line_name = feature["properties"].get("路線名", "")
        operator = feature["properties"].get("運営会社", "")
        color = LINE_COLORS.get(line_name, "#888888")

        # MultiLineString = array of line arrays
        for line_coords in feature["geometry"]["coordinates"]:
            coords = [{"lat": pt[1], "lon": pt[0]} for pt in line_coords]
            if len(coords) >= 2:
                railways.append({
                    "name": line_name,
                    "operator": operator,
                    "color": color,
                    "coords": coords,
                })

    print(f"  Loaded {len(railways)} railway segments")

    # Show unique lines found
    unique_lines = {}
    for r in railways:
        if r["name"] not in unique_lines:
            unique_lines[r["name"]] = r["color"]
    for name, color in unique_lines.items():
        print(f"    - {name} ({color})")

if os.path.exists(station_path):
    with open(station_path) as f:
        station_geojson = json.load(f)

    # Deduplicate stations (same station appears once per line that stops there)
    seen_stations = set()
    for feature in station_geojson["features"]:
        name = feature["properties"].get("駅名", "")
        line = feature["properties"].get("路線名", "")
        lon, lat = feature["geometry"]["coordinates"]

        # Only keep unique station positions (skip duplicates at same location)
        station_key = f"{name}_{round(lat, 4)}_{round(lon, 4)}"
        if station_key in seen_stations:
            continue
        seen_stations.add(station_key)

        color = LINE_COLORS.get(line, "#888888")

        stations.append({
            "name": name,
            "line": line,
            "operator": feature["properties"].get("運営会社", ""),
            "color": color,
            "lat": lat,
            "lon": lon,
        })

    print(f"  Loaded {len(stations)} unique station positions")
    for s in stations:
        print(f"    - {s['name']} ({s['line']})")

# === STEP 2E: LOAD PARK DATA ===
print("Step 2e: Loading park data...")
park_path = os.path.join(data_dir, "plateau_data", "shibuya_related",
                         "13113_shibuya-ku_pref_2023_park.geojson")
parks = []
if os.path.exists(park_path):
    with open(park_path) as f:
        park_geojson = json.load(f)
    for feature in park_geojson["features"]:
        lon, lat = feature["geometry"]["coordinates"]
        name = feature["properties"].get("公園名", "")
        area = feature["properties"].get("供用済面積", 0)
        parks.append({"name": name, "lat": lat, "lon": lon, "area": area})
    print(f"  Loaded {len(parks)} parks")
    for p in parks[:5]:
        print(f"    - {p['name']} ({p['area']}m²)")
else:
    print("  Park data not found, skipping...")

# === STEP 3: CONVERT LAT/LON TO PIXEL COORDINATES ===
print("Step 3: Converting coordinates...")

# Find the bounding box of all buildings
all_lats = [c["lat"] for b in buildings for c in b["coords"]]
all_lons = [c["lon"] for b in buildings for c in b["coords"]]

min_lat, max_lat = min(all_lats), max(all_lats)
min_lon, max_lon = min(all_lons), max(all_lons)

# Scale factor: convert tiny lat/lon differences to pixel coordinates
# At Tokyo's latitude, 1 degree ≈ 111,000 meters (lat) and ≈ 91,000 meters (lon)
METERS_PER_LEVEL = 3.5  # Average floor height in meters
SCALE = 350000  # Pixels per degree (adjust to change map size)

def latlon_to_xy(lat, lon):
    """Convert geographic coordinates to local pixel coordinates"""
    x = (lon - min_lon) * SCALE * math.cos(math.radians(lat))
    y = (max_lat - lat) * SCALE  # Flip Y (screen Y goes down)
    return x, y

# Convert all buildings to screen coordinates
for b in buildings:
    cx, cy = latlon_to_xy(b["center_lat"], b["center_lon"])
    b["screen_x"] = cx
    b["screen_y"] = cy

    # Convert polygon outline too
    b["screen_coords"] = []
    for c in b["coords"]:
        sx, sy = latlon_to_xy(c["lat"], c["lon"])
        b["screen_coords"].append({"x": sx, "y": sy})

    # Building height: use real PLATEAU height or estimate from levels
    real_height = b.get("height_m", b["levels"] * METERS_PER_LEVEL)
    b["height"] = real_height * 1.5  # Scale for visual impact

# Convert road coordinates
for r in roads:
    r["screen_coords"] = []
    for c in r["coords"]:
        sx, sy = latlon_to_xy(c["lat"], c["lon"])
        r["screen_coords"].append({"x": sx, "y": sy})

# Convert scramble crossing coordinates
scramble_area_screen = []
if scramble_area:
    for c in scramble_area:
        sx, sy = latlon_to_xy(c["lat"], c["lon"])
        scramble_area_screen.append({"x": round(sx, 1), "y": round(sy, 1)})

scramble_crossings_screen = []
for crossing in scramble_crossings:
    line = []
    for c in crossing:
        sx, sy = latlon_to_xy(c["lat"], c["lon"])
        line.append({"x": round(sx, 1), "y": round(sy, 1)})
    scramble_crossings_screen.append(line)

# Convert railway coordinates
for r in railways:
    r["screen_coords"] = []
    for c in r["coords"]:
        sx, sy = latlon_to_xy(c["lat"], c["lon"])
        r["screen_coords"].append({"x": sx, "y": sy})

# Convert station coordinates
for s in stations:
    sx, sy = latlon_to_xy(s["lat"], s["lon"])
    s["screen_x"] = sx
    s["screen_y"] = sy

# Convert park coordinates
for p in parks:
    px, py = latlon_to_xy(p["lat"], p["lon"])
    p["screen_x"] = px
    p["screen_y"] = py

# === STEP 3B: DOWNLOAD GSI SATELLITE TILES ===
# Japan's government provides FREE high-res aerial photos!
# We download tiles at build time and embed them as base64 in the HTML.
print("Step 3b: Downloading GSI satellite tiles...")

import urllib.request
import base64

GSI_ZOOM = 17  # Each tile ≈ 305m × 305m at Tokyo's latitude
GSI_TILE_SIZE = 256  # Standard web map tile size

def latlon_to_tile(lat, lon, zoom):
    """Convert lat/lon to web map tile coordinates (Mercator projection)."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def tile_to_latlon(tx, ty, zoom):
    """Convert tile coordinates back to lat/lon (top-left corner of tile)."""
    n = 2 ** zoom
    lon = tx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    return lat, lon

# Calculate which tiles cover our building area
tile_min_x, tile_min_y = latlon_to_tile(max_lat, min_lon, GSI_ZOOM)
tile_max_x, tile_max_y = latlon_to_tile(min_lat, max_lon, GSI_ZOOM)

# Add 1 tile margin around the edges
tile_min_x -= 1
tile_min_y -= 1
tile_max_x += 1
tile_max_y += 1

num_tiles = (tile_max_x - tile_min_x + 1) * (tile_max_y - tile_min_y + 1)
print(f"  Need {num_tiles} tiles at zoom {GSI_ZOOM}")

# Download and cache tiles
tile_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "plateau_data", "gsi_tiles")
os.makedirs(tile_cache_dir, exist_ok=True)

gsi_tiles = []
for tx in range(tile_min_x, tile_max_x + 1):
    for ty in range(tile_min_y, tile_max_y + 1):
        cache_path = os.path.join(tile_cache_dir, f"{GSI_ZOOM}_{tx}_{ty}.jpg")

        # Download if not cached
        if not os.path.exists(cache_path):
            url = f"https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{GSI_ZOOM}/{tx}/{ty}.jpg"
            try:
                urllib.request.urlretrieve(url, cache_path)
            except Exception as e:
                print(f"  Warning: Could not download tile {tx},{ty}: {e}")
                continue

        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")

            # Calculate tile's geographic bounds
            top_lat, left_lon = tile_to_latlon(tx, ty, GSI_ZOOM)
            bottom_lat, right_lon = tile_to_latlon(tx + 1, ty + 1, GSI_ZOOM)

            # Convert all 4 corners to our local screen coordinates
            x0, y0 = latlon_to_xy(top_lat, left_lon)     # top-left
            x1, y1 = latlon_to_xy(top_lat, right_lon)     # top-right
            x2, y2 = latlon_to_xy(bottom_lat, left_lon)   # bottom-left
            x3, y3 = latlon_to_xy(bottom_lat, right_lon)  # bottom-right

            gsi_tiles.append({
                "x0": round(x0, 1), "y0": round(y0, 1),
                "x1": round(x1, 1), "y1": round(y1, 1),
                "x2": round(x2, 1), "y2": round(y2, 1),
                "x3": round(x3, 1), "y3": round(y3, 1),
                "data": b64,
            })

print(f"  Loaded {len(gsi_tiles)} satellite tiles ({sum(len(t['data']) for t in gsi_tiles) // 1024}KB base64)")

gsi_tiles_json = json.dumps([{
    "x0": t["x0"], "y0": t["y0"],
    "x1": t["x1"], "y1": t["y1"],
    "x2": t["x2"], "y2": t["y2"],
    "x3": t["x3"], "y3": t["y3"],
    "data": t["data"],
} for t in gsi_tiles])

# === STEP 4: GENERATE THE HTML MAP ===
print("Step 4: Generating isometric HTML map...")

# Convert scramble to JSON
scramble_area_json = json.dumps(scramble_area_screen)
scramble_crossings_json = json.dumps(scramble_crossings_screen)

# Convert roads to JSON
roads_json = json.dumps([{
    "name": r["name"],
    "type": r["type"],
    "width": r["width"],
    "coords": [{"x": round(c["x"], 1), "y": round(c["y"], 1)} for c in r["screen_coords"]],
} for r in roads], indent=2)

# Convert railways to JSON
railways_json = json.dumps([{
    "name": r["name"],
    "color": r["color"],
    "coords": [{"x": round(c["x"], 1), "y": round(c["y"], 1)} for c in r["screen_coords"]],
} for r in railways])

# Convert stations to JSON
stations_json = json.dumps([{
    "name": s["name"],
    "line": s["line"],
    "color": s["color"],
    "x": round(s["screen_x"], 1),
    "y": round(s["screen_y"], 1),
} for s in stations])

# Convert parks to JSON
parks_json = json.dumps([{
    "name": p["name"],
    "area": p["area"],
    "x": round(p["screen_x"], 1),
    "y": round(p["screen_y"], 1),
} for p in parks])

# Convert buildings to JSON for embedding in HTML
buildings_json = json.dumps([{
    "name": b["name"],
    "levels": b["levels"],
    "type": b["type"],
    "usage": b.get("type", "unknown"),
    "height_m": round(b.get("height_m", 0), 1),
    "x": round(b["screen_x"], 1),
    "y": round(b["screen_y"], 1),
    "height": round(b["height"], 1),
    "coords": [{"x": round(c["x"], 1), "y": round(c["y"], 1)} for c in b["screen_coords"]],
    "hero": b.get("hero", None),
} for b in buildings], indent=2)

html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Isometric Shibuya Crossing - 16-Bit Pixel Art</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #1a1028;
            display: flex;
            flex-direction: column;
            align-items: center;
            font-family: monospace;
            color: white;
            overflow: hidden;
            image-rendering: pixelated;
        }}
        .header {{
            padding: 10px 20px;
            text-align: center;
            z-index: 10;
        }}
        h1 {{
            font-size: 18px;
            letter-spacing: 4px;
            color: #ff7799;
            margin-bottom: 4px;
            font-family: monospace;
            text-shadow: 2px 2px 0px #440022;
        }}
        .subtitle {{
            font-size: 11px;
            color: #666;
            font-family: monospace;
        }}
        canvas {{
            cursor: grab;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }}
        canvas:active {{
            cursor: grabbing;
        }}
        .info-box {{
            position: fixed;
            bottom: 15px;
            left: 15px;
            background: #1a1028ee;
            border: 2px solid #554466;
            padding: 10px 14px;
            font-size: 11px;
            color: #aa99bb;
            z-index: 10;
            font-family: monospace;
        }}
        .info-box .name {{
            color: #ff7799;
            font-size: 13px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>▶ ISOMETRIC SHIBUYA CROSSING ◀</h1>
        <div class="subtitle">16-BIT PIXEL ART &middot; {len(buildings)} buildings &middot; {len(set(r['name'] for r in railways))} train lines &middot; {len(stations)} stations &middot; {len(parks)} parks</div>
    </div>
    <canvas id="city"></canvas>
    <div class="info-box" id="info">
        <div class="name">渋谷 Shibuya Crossing</div>
        <div>Drag to pan &middot; Scroll to zoom</div>
    </div>

    <script>
        // === 16-BIT PIXEL ART ENGINE ===
        // The trick: render to a SMALL canvas, then scale up with no smoothing!
        // This is exactly how SNES/Genesis games worked.
        const PIXEL_SCALE = 3;  // Render at 1/3 resolution, scale up 3x

        const canvas = document.getElementById("city");
        const displayCtx = canvas.getContext("2d");

        // The tiny offscreen canvas where we actually draw
        const offscreen = document.createElement("canvas");
        const ctx = offscreen.getContext("2d");

        function resizeCanvases() {{
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight - 50;
            offscreen.width = Math.floor(canvas.width / PIXEL_SCALE);
            offscreen.height = Math.floor(canvas.height / PIXEL_SCALE);
            // Disable anti-aliasing on both canvases
            displayCtx.imageSmoothingEnabled = false;
            ctx.imageSmoothingEnabled = false;
        }}
        resizeCanvases();
        window.addEventListener("resize", () => {{
            resizeCanvases();
            render();
        }});

        // === DATA FROM OSM + PLATEAU ===
        const buildings = {buildings_json};
        const roads = {roads_json};
        const scrambleArea = {scramble_area_json};
        const scrambleCrossings = {scramble_crossings_json};
        const railways = {railways_json};
        const stations = {stations_json};
        const parks = {parks_json};

        // === GSI SATELLITE TILES (国土地理院) ===
        // Real aerial photos from Japan's government — embedded as base64!
        const gsiTileData = {gsi_tiles_json};

        // Load tile images from base64 data
        const gsiTiles = [];
        let gsiTilesLoaded = 0;
        for (const td of gsiTileData) {{
            const img = new Image();
            const tile = {{ img, x0: td.x0, y0: td.y0, x1: td.x1, y1: td.y1,
                           x2: td.x2, y2: td.y2, x3: td.x3, y3: td.y3 }};
            img.onload = () => {{
                gsiTilesLoaded++;
                if (gsiTilesLoaded === gsiTileData.length) render();
            }};
            img.src = "data:image/jpeg;base64," + td.data;
            gsiTiles.push(tile);
        }}

        // === CAMERA (pan & zoom) ===
        let camera = {{
            x: canvas.width / 2 + 50,
            y: -200,
            zoom: 1.3
        }};

        // === ISOMETRIC TRANSFORM ===
        function toIso(x, y) {{
            // Note: we divide by PIXEL_SCALE because we draw on the tiny canvas
            return {{
                x: ((x - y) * 0.7071 * camera.zoom + camera.x) / PIXEL_SCALE,
                y: ((x + y) * 0.3536 * camera.zoom + camera.y) / PIXEL_SCALE
            }};
        }}

        // === BUILDING HIT DETECTION ===
        // During each render, we record every building's screen bounding box.
        // Stored in render order (painter's algorithm), so LAST entry wins on overlap.
        let buildingHitBoxes = [];  // each entry: building + bounding box
        let selectedBuilding = null;

        // === 16-BIT COLOR PALETTE (Super Mario World style) ===
        // Digital twin colors: realistic concrete/steel tones with warm 16-bit feel.
        // Short buildings = warm stone/brown (older), tall = cool blue-gray (glass/steel).

        const PALETTE = {{
            // Ground colors
            road:      "#2d2d40",
            roadEdge:  "#3d3d50",
            sidewalk:  "#252535",
            crossing:  "#222233",
            stripe:    "#aaaaaa",

            // Building detail colors
            window: {{ lit: "#FFEE88", dim: "#665544", ground: "#88DDFF" }},
            floorLine: "#111111",

            // Background
            sky: "#1a1028",
        }};

        // Generate building colors based on usage type + position
        // Each building type gets a distinct material look:
        //   shop = warm terracotta/orange (colorful commercial)
        //   office = cool blue-gray steel/glass
        //   apartment/house = sandy cream (residential warmth)
        //   hotel = elegant slate blue
        //   default = height-based blend (warm→cool)
        function getBuildingColors(building) {{
            const seed = Math.abs(Math.floor(building.x * 73 + building.y * 137)) % 360;
            const heightFactor = Math.min(1, building.height_m / 150);

            // Grayscale: saturation = 0, lightness varies by height
            const hue = 0;
            const sat = 0;
            // Taller buildings = slightly darker gray (concrete/steel feel)
            const baseLightness = 58 - heightFactor * 14 + (seed % 8);

            const left  = `hsl(${{hue}}, ${{sat}}%, ${{baseLightness}}%)`;
            const right = `hsl(${{hue}}, ${{sat + 3}}%, ${{baseLightness - 12}}%)`;
            const top   = `hsl(${{hue}}, ${{sat - 4}}%, ${{baseLightness + 14}}%)`;

            return {{ left, right, top }};
        }}

        // === HELPER FUNCTIONS FOR BUILDING DETAILS ===

        // Linear interpolation: find a point between p1 and p2
        // t=0 gives p1, t=1 gives p2, t=0.5 gives the midpoint
        function lerpPoint(p1, p2, t) {{
            return {{
                x: p1.x + (p2.x - p1.x) * t,
                y: p1.y + (p2.y - p1.y) * t
            }};
        }}

        // Bilinear interpolation: find any point inside a wall face
        // u = horizontal position [0→1], v = vertical position [0→1]
        // g1,g2 = ground corners, r1,r2 = roof corners
        function bilinearPoint(g1, g2, r1, r2, u, v) {{
            const bottom = lerpPoint(g1, g2, u);
            const top = lerpPoint(r1, r2, u);
            return lerpPoint(bottom, top, v);
        }}

        // Adjust lightness of an HSL color string
        // Positive = lighter, negative = darker
        function adjustHSL(hslStr, lightnessAdjust) {{
            const match = hslStr.match(/hsl[(]([^,]+),\\s*([^%]+)%,\\s*([^%]+)%[)]/);
            if (!match) return hslStr;
            const h = parseFloat(match[1]);
            const s = parseFloat(match[2]);
            const l = Math.min(100, Math.max(0, parseFloat(match[3]) + lightnessAdjust));
            return `hsl(${{h}}, ${{s}}%, ${{l}}%)`;
        }}

        // === DITHER PATTERN for pixel-art roof textures ===
        // A 2x2 checkerboard creates classic 50% dithering
        const ditherTile = document.createElement('canvas');
        ditherTile.width = 2;
        ditherTile.height = 2;
        const ditherTileCtx = ditherTile.getContext('2d');

        // Pattern cache: avoid recreating patterns each frame
        const patternCache = new Map();

        function getDitherPattern(baseColor, darkColor) {{
            const key = baseColor + '|' + darkColor;
            if (patternCache.has(key)) return patternCache.get(key);
            ditherTileCtx.fillStyle = baseColor;
            ditherTileCtx.fillRect(0, 0, 2, 2);
            ditherTileCtx.fillStyle = darkColor;
            // Classic 50% checkerboard: darken (0,0) and (1,1)
            ditherTileCtx.fillRect(0, 0, 1, 1);
            ditherTileCtx.fillRect(1, 1, 1, 1);
            const pattern = ctx.createPattern(ditherTile, 'repeat');
            patternCache.set(key, pattern);
            return pattern;
        }}

        // Shibuya neon sign — draws a skewed parallelogram with glow
        function drawShibuyaSign(ctx, x, y, width, height, color) {{
            ctx.fillStyle = color;
            ctx.shadowBlur = 5;
            ctx.shadowColor = color;

            // Draw skewed rectangle for the billboard (2:1 isometric slope)
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + width, y + (width / 2));
            ctx.lineTo(x + width, y + (width / 2) + height);
            ctx.lineTo(x, y + height);
            ctx.closePath();
            ctx.fill();

            ctx.shadowBlur = 0;
        }}

        // Light direction — tweak x/y to move the "sun"
        // Change these two numbers to move the "sun" around.
        // Try: (0, -1) for directly above, (-1, 0) for hard left,
        //      (-0.5, -0.87) for more overhead with slight left bias
        //      (-0.7071, -0.7071) for classic top-left (current)
        const LIGHT_DIR = {{ x: -0.7071, y: -0.7071 }};

        // Determine which wall color to use based on fixed light direction
        function getWallColor(dx, dy, colors) {{
            // Edge normal = perpendicular to edge direction
            const nx = -dy;
            const ny = dx;
            // Dot product with light direction
            const dot = nx * LIGHT_DIR.x + ny * LIGHT_DIR.y;
            return dot > 0 ? colors.left : colors.right;
        }}

        // === DRAW AN ISOMETRIC BUILDING (PIXEL ART STYLE) ===
        function drawBuildingPoly(building) {{
            const coords = building.coords;
            if (coords.length < 3) return;

            // Height scaled for the tiny canvas
            const height = (building.height * camera.zoom) / PIXEL_SCALE;
            const colors = getBuildingColors(building);

            const groundPts = coords.map(c => toIso(c.x, c.y));
            const roofPts = coords.map(c => {{
                const iso = toIso(c.x, c.y);
                return {{ x: iso.x, y: iso.y - height }};
            }});

            // Record screen-space bounding box for click detection
            const allPts = [...groundPts, ...roofPts];
            const minX = Math.min(...allPts.map(p => p.x));
            const maxX = Math.max(...allPts.map(p => p.x));
            const minY = Math.min(...allPts.map(p => p.y));
            const maxY = Math.max(...allPts.map(p => p.y));
            buildingHitBoxes.push({{ building, minX, minY, maxX, maxY }});

            // Should we draw details? (skip when zoomed out too far)
            const drawDetails = (camera.zoom / PIXEL_SCALE) > 0.3 && building.levels >= 2;

            // Draw ground fill
            ctx.beginPath();
            ctx.moveTo(groundPts[0].x, groundPts[0].y);
            for (let i = 1; i < groundPts.length; i++) {{
                ctx.lineTo(groundPts[i].x, groundPts[i].y);
            }}
            ctx.closePath();
            ctx.fillStyle = colors.right;
            ctx.fill();

            // === PASS 1: Fill walls (no outlines yet) ===
            for (let i = 0; i < coords.length - 1; i++) {{
                const g1 = groundPts[i];
                const g2 = groundPts[i + 1];
                const r1 = roofPts[i];
                const r2 = roofPts[i + 1];

                ctx.beginPath();
                ctx.moveTo(g1.x, g1.y);
                ctx.lineTo(g2.x, g2.y);
                ctx.lineTo(r2.x, r2.y);
                ctx.lineTo(r1.x, r1.y);
                ctx.closePath();

                // Fixed light direction: consistent shadows across ALL buildings
                const dx = coords[i + 1].x - coords[i].x;
                const dy = coords[i + 1].y - coords[i].y;
                ctx.fillStyle = getWallColor(dx, dy, colors);
                ctx.fill();
            }}

            // === PASS 2: Draw building details (on top of wall fill) ===
            if (drawDetails) {{
                for (let i = 0; i < coords.length - 1; i++) {{
                    const g1 = groundPts[i];
                    const g2 = groundPts[i + 1];
                    const r1 = roofPts[i];
                    const r2 = roofPts[i + 1];

                    const dx = coords[i + 1].x - coords[i].x;
                    const dy = coords[i + 1].y - coords[i].y;
                    const wallColor = getWallColor(dx, dy, colors);

                    // --- Ground floor accent (usage-aware) ---
                    const isShop = building.usage === 'shop' || building.usage === 'commercial'
                                || building.usage === 'shop_house' || building.usage === 'shop_apartment';
                    const isOffice = building.usage === 'office';
                    // Shops get a taller, brighter ground floor (storefront)
                    const gfRatio = isShop ? Math.min(0.3, 2 / building.levels)
                                           : 1 / building.levels;
                    const gfTL = bilinearPoint(g1, g2, r1, r2, 0, gfRatio);
                    const gfTR = bilinearPoint(g1, g2, r1, r2, 1, gfRatio);

                    ctx.beginPath();
                    ctx.moveTo(g1.x, g1.y);
                    ctx.lineTo(g2.x, g2.y);
                    ctx.lineTo(gfTR.x, gfTR.y);
                    ctx.lineTo(gfTL.x, gfTL.y);
                    ctx.closePath();
                    // Shops = bright warm storefront, Offices = blue glass lobby
                    ctx.fillStyle = isShop ? adjustHSL(wallColor, 14)
                                 : isOffice ? adjustHSL(PALETTE.window.ground, -10)
                                 : adjustHSL(wallColor, 8);
                    ctx.fill();

                    // --- Ground floor entrance window ---
                    const entrancePt = bilinearPoint(g1, g2, r1, r2, 0.5, gfRatio * 0.5);
                    ctx.fillStyle = isShop ? "#FFCC44" : PALETTE.window.ground;
                    ctx.fillRect(Math.round(entrancePt.x) - 1, Math.round(entrancePt.y), 2, 1);

                    // --- Floor separator lines ---
                    for (let floor = 1; floor < building.levels; floor++) {{
                        const v = floor / building.levels;
                        const lineL = bilinearPoint(g1, g2, r1, r2, 0, v);
                        const lineR = bilinearPoint(g1, g2, r1, r2, 1, v);

                        ctx.beginPath();
                        ctx.moveTo(lineL.x, lineL.y);
                        ctx.lineTo(lineR.x, lineR.y);
                        ctx.strokeStyle = PALETTE.floorLine;
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }}

                    // --- Windows ---
                    // Window lit/dim pattern
                    //
                    // For each window position, decide if it's lit (bright yellow)
                    // or dim (dark brown). The variables available are:
                    //   i     = wall index (which side of the building)
                    //   floor = floor number (0 = ground, higher = upper floors)
                    //   w     = window index (0 = left window, 1 = right window)
                    //
                    // Replace the placeholder line below with your pattern logic.
                    // Ideas:
                    //   - Checkerboard:  (floor + w) % 2 === 0
                    //   - Random-ish:    (i * 7 + floor * 3 + w) % 3 !== 0
                    //   - Top floors lit: floor > building.levels / 2
                    //   - All lit:        true
                    // Window density varies by building type
                    const windowsPerFloor = isOffice ? 3 : isShop ? 1 : 2;
                    for (let floor = 1; floor < building.levels; floor++) {{
                        for (let w = 0; w < windowsPerFloor; w++) {{
                            // Space windows evenly across the wall
                            const u = (w + 1) / (windowsPerFloor + 1);
                            const vCenter = (floor + 0.5) / building.levels;
                            const pt = bilinearPoint(g1, g2, r1, r2, u, vCenter);

                            // Determine if window is lit or dim
                            const isLit = (i * 7 + floor * 3 + w) % 3 !== 0;
                            ctx.fillStyle = isLit ? PALETTE.window.lit : PALETTE.window.dim;
                            ctx.fillRect(Math.round(pt.x), Math.round(pt.y), 1, 1);
                        }}
                    }}
                }}
            }}

            // === BILLBOARD PASS: Neon signs on hero buildings ===
            // Uses drawShibuyaSign() for skewed parallelogram with shadowBlur glow
            if (building.hero && building.hero.billboards && drawDetails) {{
                // Find the widest wall face to place the sign on
                let bestWall = 0;
                let bestWidth = 0;
                for (let i = 0; i < coords.length - 1; i++) {{
                    const w = Math.abs(groundPts[i + 1].x - groundPts[i].x)
                            + Math.abs(groundPts[i + 1].y - groundPts[i].y);
                    if (w > bestWidth) {{ bestWidth = w; bestWall = i; }}
                }}
                const wi = bestWall;
                const g1 = groundPts[wi], g2 = groundPts[wi + 1];
                const r1 = roofPts[wi], r2 = roofPts[wi + 1];

                for (const bb of building.hero.billboards) {{
                    // Map billboard UV coords to the wall face position
                    const tl = bilinearPoint(g1, g2, r1, r2, bb.u0, bb.v0);
                    const tr = bilinearPoint(g1, g2, r1, r2, bb.u1, bb.v0);
                    const bl = bilinearPoint(g1, g2, r1, r2, bb.u0, bb.v1);
                    const signW = Math.abs(tr.x - tl.x) + 1;
                    const signH = Math.abs(bl.y - tl.y) + 1;

                    drawShibuyaSign(ctx, tl.x, tl.y, signW, signH, bb.color);
                }}
            }}

            // === PASS 3: Wall outlines (selective color, not pure black) ===
            for (let i = 0; i < coords.length - 1; i++) {{
                const g1 = groundPts[i];
                const g2 = groundPts[i + 1];
                const r1 = roofPts[i];
                const r2 = roofPts[i + 1];

                ctx.beginPath();
                ctx.moveTo(g1.x, g1.y);
                ctx.lineTo(g2.x, g2.y);
                ctx.lineTo(r2.x, r2.y);
                ctx.lineTo(r1.x, r1.y);
                ctx.closePath();
                // 30% darker than wall face — professional pixel art style
                const dx = coords[i + 1].x - coords[i].x;
                const dy = coords[i + 1].y - coords[i].y;
                ctx.strokeStyle = adjustHSL(getWallColor(dx, dy, colors), -20);
                ctx.lineWidth = 1;
                ctx.stroke();
            }}

            // === PASS 4: Roof with outline + dithered texture ===
            ctx.beginPath();
            ctx.moveTo(roofPts[0].x, roofPts[0].y);
            for (let i = 1; i < roofPts.length; i++) {{
                ctx.lineTo(roofPts[i].x, roofPts[i].y);
            }}
            ctx.closePath();
            ctx.fillStyle = colors.top;
            ctx.fill();

            // Dithered texture overlay on larger roofs (pixel art technique)
            if (drawDetails) {{
                // Estimate roof area with shoelace formula
                let roofArea = 0;
                for (let i = 0; i < roofPts.length; i++) {{
                    const j = (i + 1) % roofPts.length;
                    roofArea += roofPts[i].x * roofPts[j].y;
                    roofArea -= roofPts[j].x * roofPts[i].y;
                }}
                roofArea = Math.abs(roofArea) / 2;

                if (roofArea > 15) {{
                    ctx.save();
                    // Re-create the roof clip path
                    ctx.beginPath();
                    ctx.moveTo(roofPts[0].x, roofPts[0].y);
                    for (let i = 1; i < roofPts.length; i++) {{
                        ctx.lineTo(roofPts[i].x, roofPts[i].y);
                    }}
                    ctx.closePath();
                    ctx.clip();
                    const dither = getDitherPattern(colors.top, adjustHSL(colors.top, -6));
                    if (dither) {{
                        ctx.fillStyle = dither;
                        ctx.fill();
                    }}
                    ctx.restore();
                }}
            }}

            // Roof outline
            ctx.beginPath();
            ctx.moveTo(roofPts[0].x, roofPts[0].y);
            for (let i = 1; i < roofPts.length; i++) {{
                ctx.lineTo(roofPts[i].x, roofPts[i].y);
            }}
            ctx.closePath();
            ctx.strokeStyle = adjustHSL(colors.top, -20);
            ctx.lineWidth = 1;
            ctx.stroke();

            // === ROOFTOP DETAILS for hero buildings ===
            if (building.hero && building.hero.rooftop && drawDetails) {{
                const rcx = roofPts.reduce((s, p) => s + p.x, 0) / roofPts.length;
                const rcy = roofPts.reduce((s, p) => s + p.y, 0) / roofPts.length;
                const rx = Math.round(rcx);
                const ry = Math.round(rcy);

                switch (building.hero.rooftop) {{
                    case 'antenna':
                        // Tall antenna mast + crossbar
                        ctx.fillStyle = '#888888';
                        ctx.fillRect(rx, ry - 8, 1, 8);
                        ctx.fillStyle = '#AAAAAA';
                        ctx.fillRect(rx - 1, ry - 7, 3, 1);
                        ctx.fillRect(rx - 1, ry - 5, 3, 1);
                        // Red warning light at top
                        ctx.fillStyle = '#FF3333';
                        ctx.fillRect(rx, ry - 9, 1, 1);
                        break;
                    case 'helipad':
                        // White H on dark pad
                        ctx.fillStyle = '#333333';
                        ctx.fillRect(rx - 3, ry - 2, 6, 4);
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillRect(rx - 2, ry - 1, 1, 3);
                        ctx.fillRect(rx + 1, ry - 1, 1, 3);
                        ctx.fillRect(rx - 1, ry, 3, 1);
                        break;
                    case 'screen':
                        // Glowing LED screen on roof
                        ctx.fillStyle = building.hero.accent;
                        ctx.fillRect(rx - 2, ry - 2, 5, 3);
                        ctx.fillStyle = '#FFFFFF';
                        ctx.globalAlpha = 0.4;
                        ctx.fillRect(rx - 1, ry - 1, 3, 1);
                        ctx.globalAlpha = 1.0;
                        break;
                    case 'billboard_top':
                        // Vertical sign sticking up from roof
                        ctx.fillStyle = '#444444';
                        ctx.fillRect(rx - 1, ry - 5, 1, 4);
                        ctx.fillRect(rx + 1, ry - 5, 1, 4);
                        ctx.fillStyle = building.hero.accent;
                        ctx.fillRect(rx - 2, ry - 7, 5, 3);
                        break;
                    case 'sign':
                        // Flat rooftop sign
                        ctx.fillStyle = building.hero.accent;
                        ctx.fillRect(rx - 2, ry - 2, 4, 2);
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillRect(rx - 1, ry - 1, 2, 1);
                        break;
                }}
            }}
        }}

        // === DRAW BUILDING LABEL (pixel font) ===
        function drawLabel(building) {{
            if (!building.name) return;
            const iso = toIso(building.x, building.y);
            const labelY = iso.y - (building.height * camera.zoom / PIXEL_SCALE) - 4;

            // Pixel-perfect monospace font at small size
            ctx.font = `${{Math.max(5, Math.floor(4 * camera.zoom))}}px monospace`;
            ctx.fillStyle = "#dddddd";
            ctx.textAlign = "center";
            ctx.fillText(building.name, iso.x, labelY);
        }}

        // === DRAW SCRAMBLE CROSSING (pixel art) ===
        function drawScrambleCrossing() {{
            if (scrambleArea.length >= 3) {{
                const pts = scrambleArea.map(c => toIso(c.x, c.y));
                ctx.beginPath();
                ctx.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < pts.length; i++) {{
                    ctx.lineTo(pts[i].x, pts[i].y);
                }}
                ctx.closePath();
                ctx.fillStyle = PALETTE.crossing;
                ctx.fill();
            }}

            // Zebra stripes — solid white pixels, no transparency
            for (const crossing of scrambleCrossings) {{
                const pts = crossing.map(c => toIso(c.x, c.y));
                if (pts.length < 2) continue;

                for (let i = 0; i < pts.length - 1; i++) {{
                    const dx = pts[i+1].x - pts[i].x;
                    const dy = pts[i+1].y - pts[i].y;
                    const len = Math.sqrt(dx * dx + dy * dy);
                    const nx = -dy / len;
                    const ny = dx / len;
                    const stripeW = Math.max(1, Math.floor(camera.zoom));
                    const halfW = Math.max(1, Math.floor(2 * camera.zoom / PIXEL_SCALE));
                    const numStripes = Math.floor(len / (stripeW + 1));

                    for (let s = 0; s < numStripes; s++) {{
                        const t = (s * (stripeW + 1)) / len;
                        const cx = pts[i].x + dx * t;
                        const cy = pts[i].y + dy * t;

                        ctx.beginPath();
                        ctx.moveTo(cx + nx * halfW, cy + ny * halfW);
                        ctx.lineTo(cx - nx * halfW, cy - ny * halfW);
                        ctx.strokeStyle = PALETTE.stripe;
                        ctx.lineWidth = stripeW;
                        ctx.lineCap = "butt";
                        ctx.stroke();
                    }}
                }}
            }}

            // Label
            if (scrambleArea.length >= 3) {{
                const cx = scrambleArea.reduce((s, c) => s + c.x, 0) / scrambleArea.length;
                const cy = scrambleArea.reduce((s, c) => s + c.y, 0) / scrambleArea.length;
                const iso = toIso(cx, cy);
                ctx.font = `bold ${{Math.max(5, Math.floor(5 * camera.zoom))}}px monospace`;
                ctx.fillStyle = "#999999";
                ctx.textAlign = "center";
                ctx.fillText("SHIBUYA CROSSING", iso.x, iso.y);
            }}
        }}

        // === DRAW ROADS (pixel art — solid colors, no transparency) ===
        function drawRoads() {{
            for (const road of roads) {{
                const pts = road.coords.map(c => toIso(c.x, c.y));
                if (pts.length < 2) continue;

                // Road width scaled down for tiny canvas
                const w = Math.max(1, Math.floor(road.width * camera.zoom / PIXEL_SCALE));

                // Draw road border
                ctx.beginPath();
                ctx.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < pts.length; i++) {{
                    ctx.lineTo(pts[i].x, pts[i].y);
                }}
                ctx.strokeStyle = PALETTE.roadEdge;
                ctx.lineWidth = w + 1;
                ctx.lineCap = "square";  // Square caps = pixel perfect!
                ctx.lineJoin = "miter";
                ctx.stroke();

                // Draw road fill
                ctx.beginPath();
                ctx.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < pts.length; i++) {{
                    ctx.lineTo(pts[i].x, pts[i].y);
                }}
                ctx.strokeStyle = PALETTE.road;
                ctx.lineWidth = w;
                ctx.lineCap = "square";
                ctx.lineJoin = "miter";
                ctx.stroke();

                // Dashed center line for wider roads (pixel-perfect dashes)
                if (road.type !== "footway" && road.type !== "pedestrian" && w > 2) {{
                    ctx.beginPath();
                    ctx.setLineDash([2, 3]);
                    ctx.moveTo(pts[0].x, pts[0].y);
                    for (let i = 1; i < pts.length; i++) {{
                        ctx.lineTo(pts[i].x, pts[i].y);
                    }}
                    ctx.strokeStyle = "#444455";
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    ctx.setLineDash([]);
                }}
            }}

            // Road names in pixel font
            ctx.font = `${{Math.max(4, Math.floor(3 * camera.zoom))}}px monospace`;
            ctx.fillStyle = "#777788";
            ctx.textAlign = "center";
            for (const road of roads) {{
                if (!road.name || road.type === "footway") continue;
                const mid = Math.floor(road.coords.length / 2);
                const pt = toIso(road.coords[mid].x, road.coords[mid].y);
                ctx.fillText(road.name, pt.x, pt.y - 2);
            }}
        }}

        // === DRAW RAILWAY LINES (real Tokyo line colors!) ===
        function drawRailways() {{
            for (const rail of railways) {{
                const pts = rail.coords.map(c => toIso(c.x, c.y));
                if (pts.length < 2) continue;

                // Draw track bed (dark outline)
                ctx.beginPath();
                ctx.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < pts.length; i++) {{
                    ctx.lineTo(pts[i].x, pts[i].y);
                }}
                ctx.strokeStyle = "#111111";
                ctx.lineWidth = Math.max(2, Math.floor(3 * camera.zoom / PIXEL_SCALE));
                ctx.lineCap = "round";
                ctx.lineJoin = "round";
                ctx.stroke();

                // Draw colored rail line
                ctx.beginPath();
                ctx.moveTo(pts[0].x, pts[0].y);
                for (let i = 1; i < pts.length; i++) {{
                    ctx.lineTo(pts[i].x, pts[i].y);
                }}
                ctx.strokeStyle = rail.color;
                ctx.lineWidth = Math.max(1, Math.floor(2 * camera.zoom / PIXEL_SCALE));
                ctx.lineCap = "round";
                ctx.lineJoin = "round";
                ctx.stroke();
            }}
        }}

        // === DRAW STATION MARKERS ===
        function drawStations() {{
            for (const station of stations) {{
                const pt = toIso(station.x, station.y);
                const size = Math.max(2, Math.floor(3 * camera.zoom / PIXEL_SCALE));

                // Station marker design
                //
                // Each station has: station.name (Japanese), station.color (line color),
                // and screen position pt.x, pt.y.
                //
                // Draw your marker using ctx (the Canvas 2D context).
                // Available drawing commands:
                //   ctx.fillRect(x, y, width, height)  — draw a filled rectangle
                //   ctx.fillStyle = "#color"            — set fill color
                //   ctx.strokeStyle = "#color"          — set outline color
                //   ctx.lineWidth = 1                   — set line thickness
                //   ctx.beginPath() / ctx.arc(x, y, radius, 0, Math.PI*2) / ctx.fill()  — draw a circle
                //
                // Variables you can use:
                //   pt.x, pt.y  — center position of the station
                //   size        — scales with zoom level (2px at default zoom)
                //   station.color — the official line color (e.g. "#80C241" for Yamanote)
                //
                // Ideas for pixel art station markers:
                //   - A simple diamond shape (4 fillRects offset from center)
                //   - A circle with a dot in the middle (like real Tokyo Metro signs)
                //   - A small square with colored border (like JR station signs)
                //   - A cross/plus shape (classic RPG town marker)

                // Placeholder: white square with colored center
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(pt.x - size, pt.y - size, size * 2, size * 2);
                ctx.fillStyle = station.color;
                ctx.fillRect(pt.x - size + 1, pt.y - size + 1, size * 2 - 2, size * 2 - 2);

                // Station name label
                ctx.font = `bold ${{Math.max(4, Math.floor(4 * camera.zoom))}}px monospace`;
                ctx.fillStyle = "#ffffff";
                ctx.textAlign = "center";
                ctx.fillText(station.name, pt.x, pt.y - size - 2);
            }}
        }}

        // === DRAW GSI SATELLITE GROUND TILES ===
        // Uses Canvas affine transforms to project rectangular tiles into isometric space
        function drawGroundTiles() {{
            if (gsiTilesLoaded === 0) return;

            ctx.save();
            // Slightly darkened + desaturated to match pixel art aesthetic
            ctx.globalAlpha = 0.5;

            for (const tile of gsiTiles) {{
                if (!tile.img.complete) continue;

                // Convert tile corners to isometric screen positions
                // Top-left corner of tile in our coordinate system
                const origin = toIso(tile.x0, tile.y0);
                // Top-right corner (one tile width to the right)
                const right = toIso(tile.x1, tile.y1);
                // Bottom-left corner (one tile height down)
                const down = toIso(tile.x2, tile.y2);

                // Set up affine transform: maps tile pixels → isometric positions
                // This is the key math: Canvas setTransform(a,b,c,d,e,f) maps
                //   canvasX = a * srcX + c * srcY + e
                //   canvasY = b * srcX + d * srcY + f
                const tileSize = {GSI_TILE_SIZE};
                const a = (right.x - origin.x) / tileSize;
                const b = (right.y - origin.y) / tileSize;
                const c = (down.x - origin.x) / tileSize;
                const d = (down.y - origin.y) / tileSize;

                ctx.setTransform(a, b, c, d, origin.x, origin.y);
                ctx.drawImage(tile.img, 0, 0, tileSize, tileSize);
            }}

            ctx.restore();
            // Reset transform (setTransform changes it globally)
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.globalAlpha = 1.0;
        }}

        // === MAIN RENDER (offscreen → display with pixel scaling) ===
        // === PARKS: Green patches on the ground ===
        function drawParks() {{
            for (const park of parks) {{
                const iso = toIso(park.x, park.y);
                // Size based on actual park area (sqrt scale)
                const baseSize = Math.max(2, Math.floor(Math.sqrt(park.area) * 0.008
                                 * camera.zoom / PIXEL_SCALE));
                const px = Math.round(iso.x);
                const py = Math.round(iso.y);

                // Dark green ground patch (diamond shape for isometric)
                ctx.fillStyle = '#1E4D1E';
                ctx.beginPath();
                ctx.moveTo(px, py - baseSize);
                ctx.lineTo(px + baseSize * 1.5, py);
                ctx.lineTo(px, py + baseSize);
                ctx.lineTo(px - baseSize * 1.5, py);
                ctx.closePath();
                ctx.fill();

                // Lighter green center
                if (baseSize > 2) {{
                    ctx.fillStyle = '#2D6B2D';
                    ctx.beginPath();
                    const s = baseSize * 0.6;
                    ctx.moveTo(px, py - s);
                    ctx.lineTo(px + s * 1.5, py);
                    ctx.lineTo(px, py + s);
                    ctx.lineTo(px - s * 1.5, py);
                    ctx.closePath();
                    ctx.fill();
                }}

                // Tiny trees on larger parks
                if (baseSize > 3) {{
                    for (let t = 0; t < Math.min(4, baseSize); t++) {{
                        const tx = px + Math.sin(t * 2.1) * baseSize * 0.8;
                        const ty = py + Math.cos(t * 2.1) * baseSize * 0.4;
                        ctx.fillStyle = '#226622';
                        ctx.fillRect(Math.round(tx), Math.round(ty) - 2, 1, 1);
                        ctx.fillStyle = '#338833';
                        ctx.fillRect(Math.round(tx) - 1, Math.round(ty) - 1, 3, 1);
                        ctx.fillStyle = '#226622';
                        ctx.fillRect(Math.round(tx), Math.round(ty), 1, 1);
                    }}
                }}

                // Park name label (only for larger parks when zoomed in)
                if (park.area > 2000 && (camera.zoom / PIXEL_SCALE) > 0.35) {{
                    ctx.font = `${{Math.max(3, Math.floor(3 * camera.zoom / PIXEL_SCALE))}}px monospace`;
                    ctx.fillStyle = '#66AA44';
                    ctx.textAlign = 'center';
                    ctx.fillText(park.name, px, py - baseSize - 2);
                }}
            }}
        }}

        // === URBAN NOISE: Vending machines along roads ===
        function drawVendingMachines() {{
            if ((camera.zoom / PIXEL_SCALE) < 0.35) return;
            const vmColors = ['#CC2222', '#2244CC', '#22AA44', '#DD8822'];
            for (const road of roads) {{
                if (road.type === 'footway' || road.type === 'path') continue;
                const pts = road.coords;
                for (let i = 0; i < pts.length - 1; i += 3) {{
                    const mx = (pts[i].x + pts[i + 1].x) / 2;
                    const my = (pts[i].y + pts[i + 1].y) / 2;
                    const dx = pts[i + 1].x - pts[i].x;
                    const dy = pts[i + 1].y - pts[i].y;
                    const len = Math.sqrt(dx * dx + dy * dy);
                    if (len < 1) continue;
                    // Offset perpendicular to road edge
                    const ox = mx + (-dy / len) * (road.width + 2);
                    const oy = my + (dx / len) * (road.width + 2);
                    const iso = toIso(ox, oy);
                    const color = vmColors[(i * 7) % vmColors.length];
                    // Machine body
                    ctx.fillStyle = color;
                    ctx.fillRect(Math.round(iso.x), Math.round(iso.y) - 2, 1, 2);
                    // White light panel on top
                    ctx.fillStyle = '#FFFFFF';
                    ctx.fillRect(Math.round(iso.x), Math.round(iso.y) - 3, 1, 1);
                }}
            }}
        }}

        // === URBAN NOISE: Trees along pedestrian paths ===
        function drawTrees() {{
            if ((camera.zoom / PIXEL_SCALE) < 0.35) return;
            for (const road of roads) {{
                if (road.type !== 'pedestrian' && road.type !== 'living_street') continue;
                const pts = road.coords;
                for (let i = 0; i < pts.length - 1; i += 4) {{
                    const iso = toIso(pts[i].x, pts[i].y);
                    const tx = Math.round(iso.x);
                    const ty = Math.round(iso.y);
                    // Tree canopy (diamond shape)
                    ctx.fillStyle = '#336633';
                    ctx.fillRect(tx, ty - 4, 1, 1);
                    ctx.fillStyle = '#448844';
                    ctx.fillRect(tx - 1, ty - 3, 3, 1);
                    ctx.fillStyle = '#336633';
                    ctx.fillRect(tx, ty - 2, 1, 1);
                    // Trunk
                    ctx.fillStyle = '#554433';
                    ctx.fillRect(tx, ty - 1, 1, 1);
                }}
            }}
        }}

        // === URBAN NOISE: Pedestrians on scramble crossing ===
        function drawPedestrians() {{
            if ((camera.zoom / PIXEL_SCALE) < 0.35) return;
            if (scrambleArea.length < 3) return;
            const cx = scrambleArea.reduce((s, c) => s + c.x, 0) / scrambleArea.length;
            const cy = scrambleArea.reduce((s, c) => s + c.y, 0) / scrambleArea.length;
            const pedColors = ['#DDDDDD', '#AAAAAA', '#997766', '#334455',
                               '#CC8866', '#667788', '#BBAA99', '#445566'];
            for (let p = 0; p < 40; p++) {{
                // Deterministic scatter using sin/cos hash
                const px = cx + Math.sin(p * 2.4) * 18 + Math.cos(p * 1.7) * 12;
                const py = cy + Math.cos(p * 3.1) * 14 + Math.sin(p * 0.9) * 10;
                const iso = toIso(px, py);
                // 1px body + 1px head
                ctx.fillStyle = pedColors[p % pedColors.length];
                ctx.fillRect(Math.round(iso.x), Math.round(iso.y) - 1, 1, 1);
                ctx.fillStyle = '#EEDDCC';
                ctx.fillRect(Math.round(iso.x), Math.round(iso.y) - 2, 1, 1);
            }}
        }}

        function render() {{
            // Reset hit detection for this frame
            buildingHitBoxes = [];

            // Clear the tiny offscreen canvas
            ctx.clearRect(0, 0, offscreen.width, offscreen.height);

            // Fill background
            ctx.fillStyle = PALETTE.sky;
            ctx.fillRect(0, 0, offscreen.width, offscreen.height);

            // Draw satellite ground tiles (isometric projection)
            drawGroundTiles();

            // Draw parks (green patches on ground, under everything else)
            drawParks();

            // Draw railway lines (under roads and buildings)
            drawRailways();

            // Draw roads on top of satellite (under buildings)
            drawRoads();

            // Urban noise: vending machines and trees (on ground, before buildings)
            drawVendingMachines();
            drawTrees();

            // Draw the scramble crossing
            drawScrambleCrossing();

            // Pedestrians on the crossing (after crossing stripes, before buildings)
            drawPedestrians();

            // Sort: draw far buildings first (painter's algorithm)
            const sorted = [...buildings].sort((a, b) =>
                (a.x + a.y) - (b.x + b.y)
            );

            for (const b of sorted) {{
                drawBuildingPoly(b);
            }}

            // Draw labels for named buildings
            for (const b of sorted) {{
                if (b.name) drawLabel(b);
            }}

            // Draw station markers (on top of everything)
            drawStations();

            // === THE PIXEL ART MAGIC ===
            // Copy the tiny canvas to the big canvas with NO smoothing!
            displayCtx.imageSmoothingEnabled = false;
            displayCtx.clearRect(0, 0, canvas.width, canvas.height);
            displayCtx.drawImage(offscreen, 0, 0, canvas.width, canvas.height);

            // Optional: scanline effect (very subtle)
            displayCtx.fillStyle = "rgba(0,0,0,0.06)";
            for (let y = 0; y < canvas.height; y += 3) {{
                displayCtx.fillRect(0, y, canvas.width, 1);
            }}

            // Draw inspect popup on display canvas (full resolution, crisp text)
            drawInspectPopup();
        }}

        // === USAGE LABELS (for popup display) ===
        const USAGE_LABELS = {{
            'office': '業務施設 Office',
            'shop': '商業施設 Shop',
            'hotel': '宿泊施設 Hotel',
            'commercial': '商業系複合 Commercial',
            'house': '住宅 House',
            'apartment': '共同住宅 Apartment',
            'shop_house': '店舗併用住宅 Shop+House',
            'shop_apartment': '店舗併用共同住宅 Shop+Apt',
            'workshop_house': '作業所併用住宅 Workshop',
            'government': '官公庁 Government',
            'school': '文教厚生 School',
            'transport': '運輸倉庫 Transport',
            'factory': '工場 Factory',
            'unknown': '不明 Unknown',
        }};

        // TODO(human): Implement getPopupLines(building) — see Learn by Doing below
        function getPopupLines(b) {{
            return [
                {{ label: 'Height:', value: '...' }},
            ];
        }}

        // === INSPECT POPUP (drawn on display canvas at full resolution) ===
        function drawInspectPopup() {{
            if (!selectedBuilding) return;
            const b = selectedBuilding;
            const lines = getPopupLines(b);

            // Measure text to size the popup
            displayCtx.font = 'bold 14px monospace';
            const title = b.name || 'Building';
            const titleWidth = displayCtx.measureText(title).width;

            displayCtx.font = '12px monospace';
            let maxLineW = titleWidth;
            for (const line of lines) {{
                const w = displayCtx.measureText(line.label + '  ' + line.value).width;
                if (w > maxLineW) maxLineW = w;
            }}

            const padX = 14;
            const padY = 10;
            const lineH = 18;
            const boxW = maxLineW + padX * 2 + 20;
            const boxH = padY * 2 + 22 + lines.length * lineH + 8;

            // Position: top-right corner of the screen
            const boxX = canvas.width - boxW - 16;
            const boxY = 60;

            // Background — dark with pixel-art border
            displayCtx.fillStyle = '#1a1028ee';
            displayCtx.fillRect(boxX, boxY, boxW, boxH);

            // Double border (retro game style)
            displayCtx.strokeStyle = '#ff7799';
            displayCtx.lineWidth = 2;
            displayCtx.strokeRect(boxX + 1, boxY + 1, boxW - 2, boxH - 2);
            displayCtx.strokeStyle = '#554466';
            displayCtx.lineWidth = 1;
            displayCtx.strokeRect(boxX + 4, boxY + 4, boxW - 8, boxH - 8);

            // Title
            displayCtx.font = 'bold 14px monospace';
            displayCtx.fillStyle = '#ff7799';
            displayCtx.fillText(title, boxX + padX + 2, boxY + padY + 14);

            // Separator line
            const sepY = boxY + padY + 22;
            displayCtx.strokeStyle = '#554466';
            displayCtx.beginPath();
            displayCtx.moveTo(boxX + padX, sepY);
            displayCtx.lineTo(boxX + boxW - padX, sepY);
            displayCtx.stroke();

            // Data lines
            displayCtx.font = '12px monospace';
            for (let i = 0; i < lines.length; i++) {{
                const y = sepY + 6 + (i + 1) * lineH;
                displayCtx.fillStyle = '#aa99bb';
                displayCtx.fillText(lines[i].label, boxX + padX + 2, y);
                displayCtx.fillStyle = '#eeddff';
                displayCtx.fillText(lines[i].value, boxX + padX + 90, y);
            }}

            // Close hint
            displayCtx.font = '10px monospace';
            displayCtx.fillStyle = '#665577';
            displayCtx.fillText('click elsewhere to close', boxX + padX + 2, boxY + boxH - 8);
        }}

        // === PAN (drag) ===
        let dragging = false;
        let lastMouse = {{ x: 0, y: 0 }};
        let mouseDownPos = {{ x: 0, y: 0 }};

        canvas.addEventListener("mousedown", (e) => {{
            dragging = true;
            lastMouse = {{ x: e.clientX, y: e.clientY }};
            mouseDownPos = {{ x: e.clientX, y: e.clientY }};
        }});

        canvas.addEventListener("mousemove", (e) => {{
            if (!dragging) return;
            camera.x += e.clientX - lastMouse.x;
            camera.y += e.clientY - lastMouse.y;
            lastMouse = {{ x: e.clientX, y: e.clientY }};
            render();
        }});

        canvas.addEventListener("mouseup", (e) => {{
            // Distinguish click from drag: if mouse moved < 5px, it's a click
            const dx = e.clientX - mouseDownPos.x;
            const dy = e.clientY - mouseDownPos.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 5) {{
                // Convert display coordinates → offscreen coordinates
                const offX = e.clientX / PIXEL_SCALE;
                const offY = (e.clientY - 50) / PIXEL_SCALE;  // 50 = header height

                // Search hit boxes in REVERSE order (topmost building drawn last)
                let found = null;
                for (let i = buildingHitBoxes.length - 1; i >= 0; i--) {{
                    const hb = buildingHitBoxes[i];
                    if (offX >= hb.minX && offX <= hb.maxX &&
                        offY >= hb.minY && offY <= hb.maxY) {{
                        found = hb.building;
                        break;
                    }}
                }}
                selectedBuilding = found;
                render();
            }}
            dragging = false;
        }});
        canvas.addEventListener("mouseleave", () => {{ dragging = false; }});

        // === ZOOM (scroll) ===
        canvas.addEventListener("wheel", (e) => {{
            e.preventDefault();
            const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
            camera.zoom *= zoomFactor;
            camera.zoom = Math.max(0.3, Math.min(5, camera.zoom));
            render();
        }});

        // Initial render
        render();
        console.log(`Rendered ${{buildings.length}} buildings from PLATEAU + OSM data`);
    </script>
</body>
</html>"""

output_file = "/home/kenta/coding-tutor-tutorials/shibuya_osm.html"
with open(output_file, "w") as f:
    f.write(html)

print(f"\nDone! Generated: {output_file}")
print(f"  Total buildings: {len(buildings)}")
print(f"  Named buildings: {len(named)}")
print(f"  Open in browser: shibuya_osm.html")

import webbrowser

output_file = "/home/kenta/coding-tutor-tutorials/shibuya_osm.html"
with open(output_file, "w") as f:
    f.write(html)

print(f"\nDone! Generated: {output_file}")

# Automatically open in browser
webbrowser.open('file://' + output_file)
print("Opening in browser...")