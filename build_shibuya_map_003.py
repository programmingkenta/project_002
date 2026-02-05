"""
Build 3D WebGL Shibuya Crossing from PLATEAU open data.

This script:
1. Loads PLATEAU CityGML building data (real surveyed heights & footprints)
2. Loads railway, station, and road data from OSM + PLATEAU GeoJSON
3. Downloads GSI satellite tiles for the ground texture
4. Generates an interactive 3D WebGL map using Three.js

Data source: https://plateauview.mlit.go.jp/
  PLATEAU is Japan's government-led 3D city model project.
  It provides free, open CityGML data for every major city.

Unlike v001/v002 (2D isometric canvas), this uses real 3D:
  - Three.js WebGL renderer with physically-based materials
  - Extruded building geometry from PLATEAU footprints
  - Orbit camera controls (rotate, pan, zoom)
  - Raycaster click-to-inspect buildings
"""

import xml.etree.ElementTree as ET
import math
import json
import os
import urllib.request
import base64

# === CONFIGURATION ===
CROSSING_LAT = 35.6594    # Shibuya Crossing latitude
CROSSING_LON = 139.7006   # Shibuya Crossing longitude
RADIUS_M = 200            # Include buildings within 200m of crossing center
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Meters per degree at Tokyo's latitude (~35.66°N)
M_PER_DEG_LAT = 111000
M_PER_DEG_LON = 111000 * math.cos(math.radians(CROSSING_LAT))  # ≈ 91,000


def latlon_to_meters(lat, lon):
    """Convert lat/lon to meters from Shibuya Crossing center.

    Returns (x, z) in Three.js convention:
      x = East (positive)
      z = South (positive), so North = negative z
    """
    x = (lon - CROSSING_LON) * M_PER_DEG_LON
    z = -(lat - CROSSING_LAT) * M_PER_DEG_LAT
    return x, z


# ============================================================
# STEP 1: LOAD PLATEAU BUILDING DATA
# ============================================================
print("Step 1: Loading PLATEAU building data...")

plateau_path = os.path.join(SCRIPT_DIR, "plateau_data",
                            "shibuya_crossing_buildings.json")

with open(plateau_path) as f:
    all_plateau = json.load(f)

USAGE_MAP = {
    "401": "office",    "402": "shop",        "403": "hotel",
    "404": "commercial", "411": "house",       "412": "apartment",
    "413": "shop_house", "414": "shop_apartment", "415": "workshop_house",
    "421": "government", "422": "school",      "431": "transport",
    "441": "factory",    "461": "unknown",
}

buildings = []
for pb in all_plateau:
    dist = pb.get("distance_from_crossing", 999)
    if dist > RADIUS_M:
        continue
    if pb.get("height", 0) <= 0 or pb.get("height", 0) > 500:
        continue
    if "footprint" not in pb or len(pb["footprint"]) < 3:
        continue

    # Convert footprint to meters from crossing center
    footprint_m = []
    for pt in pb["footprint"]:
        mx, mz = latlon_to_meters(pt[0], pt[1])
        footprint_m.append({"x": round(mx, 2), "z": round(mz, 2)})

    # Center point in meters
    center_lat = pb.get("center_lat",
                        sum(pt[0] for pt in pb["footprint"]) / len(pb["footprint"]))
    center_lon = pb.get("center_lon",
                        sum(pt[1] for pt in pb["footprint"]) / len(pb["footprint"]))
    cx, cz = latlon_to_meters(center_lat, center_lon)

    floors = pb.get("floors", max(1, int(pb["height"] / 3.5)))
    if floors >= 9999:
        floors = max(1, int(pb["height"] / 3.5))

    buildings.append({
        "id": pb.get("id", ""),
        "name": "",  # Will be filled from OSM names below
        "height": pb["height"],
        "floors": floors,
        "usage": USAGE_MAP.get(pb.get("usage_code", "461"), "unknown"),
        "cx": round(cx, 2),
        "cz": round(cz, 2),
        "footprint": footprint_m,
        "distance": round(dist, 1),
    })

print(f"  Loaded {len(buildings)} buildings within {RADIUS_M}m")

# Show height distribution
heights = [b["height"] for b in buildings]
print(f"  Height range: {min(heights):.0f}m – {max(heights):.0f}m")
usage_counts = {}
for b in buildings:
    usage_counts[b["usage"]] = usage_counts.get(b["usage"], 0) + 1
for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
    print(f"    {usage}: {count}")


# ============================================================
# STEP 2: PARSE OSM FILE (for road data + building names)
# ============================================================
print("Step 2: Parsing OSM file...")

osm_file = "/home/kenta/Downloads/Shibuya Crossing Map.osm"
tree = ET.parse(osm_file)
root = tree.getroot()

# Build node lookup
nodes = {}
for node in root.findall("node"):
    node_id = node.get("id")
    lat = float(node.get("lat"))
    lon = float(node.get("lon"))
    nodes[node_id] = {"lat": lat, "lon": lon}

print(f"  Found {len(nodes)} OSM nodes")

# --- Extract OSM named buildings (to match names to PLATEAU) ---
osm_named_buildings = []
for way in root.findall("way"):
    tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
    if "building" not in tags:
        continue
    name = tags.get("name:en") or tags.get("name") or ""
    if not name:
        continue

    node_refs = [nd.get("ref") for nd in way.findall("nd")]
    coords = [nodes[ref] for ref in node_refs if ref in nodes]
    if len(coords) < 3:
        continue

    center_lat = sum(c["lat"] for c in coords) / len(coords)
    center_lon = sum(c["lon"] for c in coords) / len(coords)
    osm_named_buildings.append({"name": name, "lat": center_lat, "lon": center_lon})

# Match OSM names → nearest PLATEAU building
for osm_b in osm_named_buildings:
    ox, oz = latlon_to_meters(osm_b["lat"], osm_b["lon"])
    best_dist = 999999
    best_match = None
    for pb in buildings:
        dx = ox - pb["cx"]
        dz = oz - pb["cz"]
        d = math.sqrt(dx**2 + dz**2)
        if d < best_dist:
            best_dist = d
            best_match = pb
    if best_match and best_dist < 30:
        best_match["name"] = osm_b["name"]

named = [b for b in buildings if b["name"]]
print(f"  Matched {len(named)} building names from OSM:")
for b in named:
    print(f"    - {b['name']} ({b['height']:.0f}m, {b['floors']}F, {b['usage']})")

# --- Extract roads ---
print("  Extracting roads...")
roads = []
for way in root.findall("way"):
    tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
    highway_type = tags.get("highway")
    if not highway_type:
        continue
    if highway_type in ("bus_stop", "traffic_signals", "crossing"):
        continue

    node_refs = [nd.get("ref") for nd in way.findall("nd")]
    coords = [nodes[ref] for ref in node_refs if ref in nodes]
    if len(coords) < 2:
        continue

    name = tags.get("name:en") or tags.get("name") or ""

    # Road width in meters
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

    # Convert to meters
    road_coords = []
    for c in coords:
        mx, mz = latlon_to_meters(c["lat"], c["lon"])
        road_coords.append({"x": round(mx, 2), "z": round(mz, 2)})

    roads.append({
        "name": name,
        "type": highway_type,
        "width": width,
        "coords": road_coords,
    })

print(f"  Found {len(roads)} roads/paths")

# --- Extract scramble crossing ---
print("  Extracting scramble crossing...")
scramble_area = []
scramble_crossings = []

for way in root.findall("way"):
    tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
    is_scramble = tags.get("crossing:scramble") == "yes"
    is_area = tags.get("area") == "yes"
    alt_name = tags.get("alt_name:en", "")

    if "Scramble Crossing" in alt_name or (is_area and "junction" in tags):
        node_refs = [nd.get("ref") for nd in way.findall("nd")]
        coords = [nodes[ref] for ref in node_refs if ref in nodes]
        if len(coords) >= 3:
            scramble_area = []
            for c in coords:
                mx, mz = latlon_to_meters(c["lat"], c["lon"])
                scramble_area.append({"x": round(mx, 2), "z": round(mz, 2)})
            print(f"  Found scramble crossing area ({len(coords)} pts)")

    if is_scramble and tags.get("highway") == "footway":
        node_refs = [nd.get("ref") for nd in way.findall("nd")]
        coords = [nodes[ref] for ref in node_refs if ref in nodes]
        if len(coords) >= 2:
            line = []
            for c in coords:
                mx, mz = latlon_to_meters(c["lat"], c["lon"])
                line.append({"x": round(mx, 2), "z": round(mz, 2)})
            scramble_crossings.append(line)

print(f"  Found {len(scramble_crossings)} crossing paths")


# ============================================================
# STEP 3: LOAD RAILWAY & STATION DATA
# ============================================================
print("Step 3: Loading railway and station data...")

railway_path = os.path.join(SCRIPT_DIR, "plateau_data", "shibuya_related",
                            "13113_shibuya-ku_pref_2023_railway.geojson")
station_path = os.path.join(SCRIPT_DIR, "plateau_data", "shibuya_related",
                            "13113_shibuya-ku_pref_2023_station.geojson")

LINE_COLORS = {
    "山手線":         "#80C241",
    "中央線":         "#F15A22",
    "井の頭線":       "#9B7CB6",
    "京王線":         "#DD0033",
    "小田原線":       "#1E72B7",
    "田園都市線":     "#009944",
    "東横線":         "#E5171F",
    "3号線銀座線":    "#F39700",
    "11号線半蔵門線": "#8F76D6",
    "13号線副都心線": "#9C5E31",
    "9号線千代田線":  "#00A650",
    "2号線日比谷線":  "#B5B5AC",
    "10号線新宿線":   "#6CBB5A",
    "12号線大江戸線": "#B6007A",
}

railways = []
stations = []

if os.path.exists(railway_path):
    with open(railway_path) as f:
        railway_geojson = json.load(f)

    for feature in railway_geojson["features"]:
        line_name = feature["properties"].get("路線名", "")
        operator = feature["properties"].get("運営会社", "")
        color = LINE_COLORS.get(line_name, "#888888")

        for line_coords in feature["geometry"]["coordinates"]:
            coords_m = []
            for pt in line_coords:
                mx, mz = latlon_to_meters(pt[1], pt[0])
                coords_m.append({"x": round(mx, 2), "z": round(mz, 2)})
            if len(coords_m) >= 2:
                railways.append({
                    "name": line_name,
                    "operator": operator,
                    "color": color,
                    "coords": coords_m,
                })

    print(f"  Loaded {len(railways)} railway segments")
    unique_lines = {}
    for r in railways:
        if r["name"] not in unique_lines:
            unique_lines[r["name"]] = r["color"]
    for name, color in unique_lines.items():
        print(f"    - {name} ({color})")

if os.path.exists(station_path):
    with open(station_path) as f:
        station_geojson = json.load(f)

    seen = set()
    for feature in station_geojson["features"]:
        name = feature["properties"].get("駅名", "")
        line = feature["properties"].get("路線名", "")
        lon, lat = feature["geometry"]["coordinates"]

        key = f"{name}_{round(lat, 4)}_{round(lon, 4)}"
        if key in seen:
            continue
        seen.add(key)

        mx, mz = latlon_to_meters(lat, lon)
        color = LINE_COLORS.get(line, "#888888")

        stations.append({
            "name": name,
            "line": line,
            "color": color,
            "x": round(mx, 2),
            "z": round(mz, 2),
        })

    print(f"  Loaded {len(stations)} unique station positions")


# ============================================================
# STEP 4: DOWNLOAD GSI SATELLITE TILES
# ============================================================
print("Step 4: Downloading GSI satellite tiles...")

GSI_ZOOM = 18  # Higher zoom than v002 for 200m radius detail
GSI_TILE_SIZE = 256

# Bounding box: 200m radius around crossing
margin = RADIUS_M + 50  # 50m extra margin
bb_min_lat = CROSSING_LAT - margin / M_PER_DEG_LAT
bb_max_lat = CROSSING_LAT + margin / M_PER_DEG_LAT
bb_min_lon = CROSSING_LON - margin / M_PER_DEG_LON
bb_max_lon = CROSSING_LON + margin / M_PER_DEG_LON


def latlon_to_tile(lat, lon, zoom):
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0/math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_to_latlon(tx, ty, zoom):
    n = 2 ** zoom
    lon = tx / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty / n))))
    return lat, lon


tile_min_x, tile_min_y = latlon_to_tile(bb_max_lat, bb_min_lon, GSI_ZOOM)
tile_max_x, tile_max_y = latlon_to_tile(bb_min_lat, bb_max_lon, GSI_ZOOM)

num_tiles = (tile_max_x - tile_min_x + 1) * (tile_max_y - tile_min_y + 1)
print(f"  Need {num_tiles} tiles at zoom {GSI_ZOOM}")

tile_cache_dir = os.path.join(SCRIPT_DIR, "plateau_data", "gsi_tiles")
os.makedirs(tile_cache_dir, exist_ok=True)

gsi_tiles = []
for tx in range(tile_min_x, tile_max_x + 1):
    for ty in range(tile_min_y, tile_max_y + 1):
        cache_path = os.path.join(tile_cache_dir, f"{GSI_ZOOM}_{tx}_{ty}.jpg")

        if not os.path.exists(cache_path):
            url = f"https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{GSI_ZOOM}/{tx}/{ty}.jpg"
            try:
                urllib.request.urlretrieve(url, cache_path)
            except Exception as e:
                print(f"  Warning: tile {tx},{ty}: {e}")
                continue

        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")

            # Tile corner coordinates in meters
            tl_lat, tl_lon = tile_to_latlon(tx, ty, GSI_ZOOM)
            tr_lat, tr_lon = tile_to_latlon(tx + 1, ty, GSI_ZOOM)
            bl_lat, bl_lon = tile_to_latlon(tx, ty + 1, GSI_ZOOM)
            br_lat, br_lon = tile_to_latlon(tx + 1, ty + 1, GSI_ZOOM)

            tl_x, tl_z = latlon_to_meters(tl_lat, tl_lon)
            tr_x, tr_z = latlon_to_meters(tr_lat, tr_lon)
            bl_x, bl_z = latlon_to_meters(bl_lat, bl_lon)
            br_x, br_z = latlon_to_meters(br_lat, br_lon)

            # Center and size (tiles are near-rectangular at this scale)
            center_x = (tl_x + br_x) / 2
            center_z = (tl_z + br_z) / 2
            width = abs(tr_x - tl_x)
            depth = abs(bl_z - tl_z)

            gsi_tiles.append({
                "cx": round(center_x, 2),
                "cz": round(center_z, 2),
                "width": round(width, 2),
                "depth": round(depth, 2),
                "data": b64,
            })

total_kb = sum(len(t["data"]) for t in gsi_tiles) // 1024
print(f"  Loaded {len(gsi_tiles)} satellite tiles ({total_kb}KB base64)")


# ============================================================
# STEP 5: SERIALIZE DATA TO JSON
# ============================================================
print("Step 5: Serializing data...")

buildings_json = json.dumps(buildings, indent=2)
roads_json = json.dumps(roads)
scramble_area_json = json.dumps(scramble_area)
scramble_crossings_json = json.dumps(scramble_crossings)
railways_json = json.dumps(railways)
stations_json = json.dumps(stations)
gsi_tiles_json = json.dumps(gsi_tiles)

# Railway legend data (unique lines with colors)
legend_lines = {}
for r in railways:
    if r["name"] not in legend_lines:
        legend_lines[r["name"]] = r["color"]
legend_json = json.dumps(legend_lines)


# ============================================================
# STEP 6: GENERATE HTML WITH THREE.JS
# ============================================================
print("Step 6: Generating 3D WebGL HTML...")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>3D Shibuya Crossing — PLATEAU Data</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ overflow: hidden; background: #0a0a1a; font-family: monospace; }}
        canvas {{ display: block; }}

        #info-panel {{
            position: fixed;
            top: 16px;
            right: 16px;
            background: rgba(10, 10, 26, 0.92);
            border: 1px solid #334;
            border-radius: 8px;
            padding: 16px 20px;
            color: #ccc;
            font-size: 13px;
            min-width: 240px;
            max-width: 320px;
            z-index: 10;
            display: none;
            backdrop-filter: blur(8px);
        }}
        #info-panel .title {{
            color: #ff7799;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        #info-panel .row {{
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            border-bottom: 1px solid #1a1a2e;
        }}
        #info-panel .label {{ color: #888; }}
        #info-panel .value {{ color: #eee; text-align: right; }}
        #info-panel .close {{
            position: absolute;
            top: 8px;
            right: 12px;
            color: #666;
            cursor: pointer;
            font-size: 16px;
        }}
        #info-panel .close:hover {{ color: #ff7799; }}

        #legend {{
            position: fixed;
            bottom: 16px;
            left: 16px;
            background: rgba(10, 10, 26, 0.88);
            border: 1px solid #334;
            border-radius: 8px;
            padding: 12px 16px;
            color: #aaa;
            font-size: 11px;
            z-index: 10;
            backdrop-filter: blur(8px);
        }}
        #legend h3 {{
            color: #ff7799;
            font-size: 13px;
            margin-bottom: 8px;
        }}
        .legend-line {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 2px 0;
        }}
        .legend-swatch {{
            width: 20px;
            height: 4px;
            border-radius: 2px;
        }}

        #hud {{
            position: fixed;
            top: 16px;
            left: 16px;
            color: #556;
            font-size: 11px;
            z-index: 10;
        }}
        #hud h1 {{
            color: #ff7799;
            font-size: 16px;
            letter-spacing: 2px;
            margin-bottom: 4px;
        }}
        #hud .sub {{ color: #556; }}

        #controls-hint {{
            position: fixed;
            bottom: 16px;
            right: 16px;
            color: #445;
            font-size: 11px;
            text-align: right;
            z-index: 10;
        }}
    </style>
</head>
<body>
    <div id="hud">
        <h1>SHIBUYA CROSSING 3D</h1>
        <div class="sub">PLATEAU Open Data &middot; {len(buildings)} buildings &middot; {RADIUS_M}m radius</div>
    </div>

    <div id="info-panel">
        <span class="close" onclick="document.getElementById('info-panel').style.display='none'">&times;</span>
        <div class="title" id="info-title">Building</div>
        <div id="info-rows"></div>
    </div>

    <div id="legend">
        <h3>Railway Lines</h3>
        <div id="legend-lines"></div>
    </div>

    <div id="controls-hint">
        Left drag: rotate &middot; Right drag: pan<br>
        Scroll: zoom &middot; Click building: inspect
    </div>

    <script type="importmap">
    {{
        "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"
        }}
    }}
    </script>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ Line2 }} from 'three/addons/lines/Line2.js';
        import {{ LineMaterial }} from 'three/addons/lines/LineMaterial.js';
        import {{ LineGeometry }} from 'three/addons/lines/LineGeometry.js';

        // === DATA (embedded from Python build) ===
        const buildings = {buildings_json};
        const roads = {roads_json};
        const scrambleArea = {scramble_area_json};
        const scrambleCrossings = {scramble_crossings_json};
        const railways = {railways_json};
        const stationData = {stations_json};
        const gsiTileData = {gsi_tiles_json};
        const legendLines = {legend_json};

        // === USAGE LABELS ===
        const USAGE_LABELS = {{
            'office': 'Office 業務施設',
            'shop': 'Shop 商業施設',
            'hotel': 'Hotel 宿泊施設',
            'commercial': 'Commercial 商業複合',
            'house': 'House 住宅',
            'apartment': 'Apartment 共同住宅',
            'shop_house': 'Shop+House 店舗併用',
            'shop_apartment': 'Shop+Apt 店舗共同住宅',
            'workshop_house': 'Workshop 作業所併用',
            'government': 'Government 官公庁',
            'school': 'School 文教厚生',
            'transport': 'Transport 運輸倉庫',
            'factory': 'Factory 工場',
            'unknown': 'Unknown 不明',
        }};

        // === SCENE SETUP ===
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0a1a);
        scene.fog = new THREE.FogExp2(0x0a0a1a, 0.0015);

        const camera = new THREE.PerspectiveCamera(
            55, window.innerWidth / window.innerHeight, 0.5, 2000
        );
        camera.position.set(180, 220, 260);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;
        document.body.appendChild(renderer.domElement);

        // === LIGHTING ===
        // Hemisphere: sky blue from above, warm bounce from ground
        const hemiLight = new THREE.HemisphereLight(0x8899bb, 0x444433, 0.6);
        scene.add(hemiLight);

        // Main directional (sun-like)
        const dirLight = new THREE.DirectionalLight(0xffeedd, 1.5);
        dirLight.position.set(80, 200, 100);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        dirLight.shadow.camera.left = -250;
        dirLight.shadow.camera.right = 250;
        dirLight.shadow.camera.top = 250;
        dirLight.shadow.camera.bottom = -250;
        dirLight.shadow.camera.near = 1;
        dirLight.shadow.camera.far = 600;
        dirLight.shadow.bias = -0.001;
        scene.add(dirLight);

        // Subtle fill light from the opposite side
        const fillLight = new THREE.DirectionalLight(0x8888cc, 0.3);
        fillLight.position.set(-60, 100, -80);
        scene.add(fillLight);

        // === CAMERA CONTROLS ===
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 30, 0);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.maxPolarAngle = Math.PI / 2 - 0.02;
        controls.minDistance = 30;
        controls.maxDistance = 800;
        controls.update();

        // === GROUND PLANE ===
        const groundGeo = new THREE.PlaneGeometry(600, 600);
        const groundMat = new THREE.MeshStandardMaterial({{
            color: 0x1a1a2e,
            roughness: 0.95,
            metalness: 0.0,
        }});
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.1;
        ground.receiveShadow = true;
        scene.add(ground);

        // === GSI SATELLITE TILES (ground texture) ===
        for (const tile of gsiTileData) {{
            const img = new Image();
            img.src = 'data:image/jpeg;base64,' + tile.data;
            img.onload = () => {{
                const texture = new THREE.Texture(img);
                texture.needsUpdate = true;
                texture.colorSpace = THREE.SRGBColorSpace;

                const mat = new THREE.MeshBasicMaterial({{
                    map: texture,
                    transparent: true,
                    opacity: 0.5,
                    depthWrite: false,
                }});
                const geo = new THREE.PlaneGeometry(tile.width, tile.depth);
                const mesh = new THREE.Mesh(geo, mat);
                mesh.rotation.x = -Math.PI / 2;
                mesh.position.set(tile.cx, 0.01, tile.cz);
                scene.add(mesh);
            }};
        }}

        // === BUILDING MATERIAL FUNCTION ===
        // TODO(human): Design building materials based on usage type!
        //
        // This function receives a building object with these properties:
        //   building.usage  — 'office', 'shop', 'hotel', 'apartment', 'house', etc.
        //   building.height — real height in meters (3.4m to 220m)
        //   building.floors — number of floors
        //   building.name   — building name (may be empty)
        //
        // Return a THREE.MeshStandardMaterial with properties:
        //   color:     hex color (e.g. 0x667788)
        //   roughness: 0.0 (mirror) to 1.0 (matte)
        //   metalness: 0.0 (plastic/concrete) to 1.0 (metal)
        //   transparent, opacity: for glass-like buildings
        //
        // Design ideas:
        //   - Office towers: blue-gray glass, low roughness (0.1-0.3), slight metalness
        //   - Shops: warm terracotta/orange, high roughness (matte painted walls)
        //   - Hotels: elegant dark slate, medium roughness
        //   - Apartments: cream/beige, high roughness (concrete)
        //   - Tall buildings (>100m): glass curtain wall look
        //   - Named landmarks: special accent colors?
        //
        function createBuildingMaterial(building) {{
            // Placeholder: gray concrete — replace with your design!
            return new THREE.MeshStandardMaterial({{
                color: 0x556677,
                roughness: 0.8,
                metalness: 0.1,
                side: THREE.DoubleSide,
            }});
        }}

        // === CREATE BUILDING MESHES ===
        const buildingMeshes = [];

        for (const b of buildings) {{
            if (b.footprint.length < 3) continue;

            // Create 2D shape from footprint (relative to building center)
            const shape = new THREE.Shape();
            const fp = b.footprint;
            shape.moveTo(fp[0].x - b.cx, -(fp[0].z - b.cz));
            for (let i = 1; i < fp.length; i++) {{
                shape.lineTo(fp[i].x - b.cx, -(fp[i].z - b.cz));
            }}

            // Extrude upward
            const geometry = new THREE.ExtrudeGeometry(shape, {{
                depth: b.height,
                bevelEnabled: false,
            }});
            // Rotate so extrusion goes up (Y axis) instead of forward (Z axis)
            geometry.rotateX(-Math.PI / 2);

            const material = createBuildingMaterial(b);
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(b.cx, 0, b.cz);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            mesh.userData = b;
            scene.add(mesh);
            buildingMeshes.push(mesh);
        }}

        console.log(`Created ${{buildingMeshes.length}} building meshes`);

        // === BUILDING NAME LABELS (CSS2D would be better, but let's use sprites) ===
        for (const b of buildings) {{
            if (!b.name) continue;
            const canvas2d = document.createElement('canvas');
            const ctx2d = canvas2d.getContext('2d');
            canvas2d.width = 512;
            canvas2d.height = 64;

            ctx2d.fillStyle = 'transparent';
            ctx2d.fillRect(0, 0, 512, 64);
            ctx2d.font = 'bold 28px monospace';
            ctx2d.fillStyle = '#ffffff';
            ctx2d.textAlign = 'center';
            ctx2d.fillText(b.name, 256, 40);

            const texture = new THREE.CanvasTexture(canvas2d);
            texture.colorSpace = THREE.SRGBColorSpace;
            const spriteMat = new THREE.SpriteMaterial({{
                map: texture,
                transparent: true,
                depthTest: false,
            }});
            const sprite = new THREE.Sprite(spriteMat);
            sprite.position.set(b.cx, b.height + 12, b.cz);
            sprite.scale.set(40, 5, 1);
            scene.add(sprite);
        }}

        // === ROADS (flat ribbons on the ground) ===
        for (const road of roads) {{
            if (road.coords.length < 2) continue;

            // Create line positions
            const positions = [];
            for (const pt of road.coords) {{
                positions.push(pt.x, 0.15, pt.z);
            }}

            const geo = new LineGeometry();
            geo.setPositions(positions);

            const color = road.type === 'footway' ? 0x333344
                        : road.type === 'pedestrian' ? 0x334444
                        : 0x3d3d50;

            const mat = new LineMaterial({{
                color: color,
                linewidth: Math.max(1, road.width * 0.4),
                resolution: new THREE.Vector2(window.innerWidth, window.innerHeight),
            }});

            const line = new Line2(geo, mat);
            scene.add(line);
        }}

        // === SCRAMBLE CROSSING (white stripes on ground) ===
        for (const crossing of scrambleCrossings) {{
            if (crossing.length < 2) continue;
            const positions = [];
            for (const pt of crossing) {{
                positions.push(pt.x, 0.2, pt.z);
            }}
            const geo = new LineGeometry();
            geo.setPositions(positions);
            const mat = new LineMaterial({{
                color: 0xaaaaaa,
                linewidth: 3,
                resolution: new THREE.Vector2(window.innerWidth, window.innerHeight),
            }});
            scene.add(new Line2(geo, mat));
        }}

        // Scramble area (semi-transparent dark polygon)
        if (scrambleArea.length >= 3) {{
            const scrambleShape = new THREE.Shape();
            scrambleShape.moveTo(scrambleArea[0].x, -scrambleArea[0].z);
            for (let i = 1; i < scrambleArea.length; i++) {{
                scrambleShape.lineTo(scrambleArea[i].x, -scrambleArea[i].z);
            }}
            const scrambleGeo = new THREE.ShapeGeometry(scrambleShape);
            scrambleGeo.rotateX(-Math.PI / 2);
            const scrambleMat = new THREE.MeshBasicMaterial({{
                color: 0x222233,
                transparent: true,
                opacity: 0.7,
                depthWrite: false,
            }});
            const scrambleMesh = new THREE.Mesh(scrambleGeo, scrambleMat);
            scrambleMesh.position.y = 0.05;
            scene.add(scrambleMesh);
        }}

        // === RAILWAY LINES (elevated colored lines) ===
        const RAIL_ELEVATION = 8;  // Elevated above street level

        for (const rail of railways) {{
            if (rail.coords.length < 2) continue;
            const positions = [];
            for (const pt of rail.coords) {{
                positions.push(pt.x, RAIL_ELEVATION, pt.z);
            }}

            // Dark track bed
            const bedGeo = new LineGeometry();
            bedGeo.setPositions(positions);
            const bedMat = new LineMaterial({{
                color: 0x111111,
                linewidth: 4,
                resolution: new THREE.Vector2(window.innerWidth, window.innerHeight),
            }});
            scene.add(new Line2(bedGeo, bedMat));

            // Colored rail line
            const railGeo = new LineGeometry();
            railGeo.setPositions(positions);
            const railMat = new LineMaterial({{
                color: new THREE.Color(rail.color).getHex(),
                linewidth: 2.5,
                resolution: new THREE.Vector2(window.innerWidth, window.innerHeight),
            }});
            scene.add(new Line2(railGeo, railMat));
        }}

        // === STATION MARKERS (glowing spheres) ===
        for (const station of stationData) {{
            const stationColor = new THREE.Color(station.color);

            // Sphere marker
            const sphereGeo = new THREE.SphereGeometry(4, 16, 12);
            const sphereMat = new THREE.MeshStandardMaterial({{
                color: stationColor,
                emissive: stationColor,
                emissiveIntensity: 0.5,
                roughness: 0.3,
                metalness: 0.6,
            }});
            const sphere = new THREE.Mesh(sphereGeo, sphereMat);
            sphere.position.set(station.x, RAIL_ELEVATION + 4, station.z);
            scene.add(sphere);

            // Station name label
            const canvas2d = document.createElement('canvas');
            const ctx2d = canvas2d.getContext('2d');
            canvas2d.width = 256;
            canvas2d.height = 64;
            ctx2d.font = 'bold 24px monospace';
            ctx2d.fillStyle = '#ffffff';
            ctx2d.textAlign = 'center';
            ctx2d.fillText(station.name, 128, 40);

            const texture = new THREE.CanvasTexture(canvas2d);
            texture.colorSpace = THREE.SRGBColorSpace;
            const spriteMat = new THREE.SpriteMaterial({{
                map: texture,
                transparent: true,
                depthTest: false,
            }});
            const sprite = new THREE.Sprite(spriteMat);
            sprite.position.set(station.x, RAIL_ELEVATION + 14, station.z);
            sprite.scale.set(30, 7.5, 1);
            scene.add(sprite);
        }}

        // === 200M RADIUS CIRCLE (visual boundary) ===
        const circleGeo = new THREE.RingGeometry({RADIUS_M} - 0.5, {RADIUS_M} + 0.5, 128);
        const circleMat = new THREE.MeshBasicMaterial({{
            color: 0xff7799,
            transparent: true,
            opacity: 0.15,
            side: THREE.DoubleSide,
            depthWrite: false,
        }});
        const circle = new THREE.Mesh(circleGeo, circleMat);
        circle.rotation.x = -Math.PI / 2;
        circle.position.y = 0.02;
        scene.add(circle);

        // === RAYCASTER (click-to-inspect) ===
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        let mouseDownPos = {{ x: 0, y: 0 }};

        renderer.domElement.addEventListener('mousedown', (e) => {{
            mouseDownPos = {{ x: e.clientX, y: e.clientY }};
        }});

        renderer.domElement.addEventListener('mouseup', (e) => {{
            const dx = e.clientX - mouseDownPos.x;
            const dy = e.clientY - mouseDownPos.y;
            if (Math.sqrt(dx*dx + dy*dy) > 5) return;  // Was a drag, not a click

            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const hits = raycaster.intersectObjects(buildingMeshes);

            if (hits.length > 0) {{
                showBuildingInfo(hits[0].object.userData);
            }} else {{
                document.getElementById('info-panel').style.display = 'none';
            }}
        }});

        function showBuildingInfo(b) {{
            const panel = document.getElementById('info-panel');
            document.getElementById('info-title').textContent = b.name || 'Building';

            const rows = [
                ['Height', b.height.toFixed(1) + 'm'],
                ['Floors', b.floors + 'F'],
                ['Usage', USAGE_LABELS[b.usage] || b.usage],
                ['Distance', b.distance + 'm from crossing'],
                ['ID', b.id.replace('bldg_', '').slice(0, 12) + '...'],
            ];

            const container = document.getElementById('info-rows');
            container.innerHTML = '';
            for (const [label, value] of rows) {{
                const row = document.createElement('div');
                row.className = 'row';
                row.innerHTML = `<span class="label">${{label}}</span><span class="value">${{value}}</span>`;
                container.appendChild(row);
            }}

            panel.style.display = 'block';
        }}

        // === RAILWAY LEGEND ===
        const legendContainer = document.getElementById('legend-lines');
        for (const [name, color] of Object.entries(legendLines)) {{
            const div = document.createElement('div');
            div.className = 'legend-line';
            div.innerHTML = `<span class="legend-swatch" style="background:${{color}}"></span><span>${{name}}</span>`;
            legendContainer.appendChild(div);
        }}

        // === WINDOW RESIZE ===
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});

        // === ANIMATION LOOP ===
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        console.log('3D Shibuya Crossing loaded — PLATEAU open data');
        console.log(`${{buildings.length}} buildings, ${{railways.length}} rail segments, ${{stationData.length}} stations`);
    </script>
</body>
</html>"""

output_file = os.path.join(SCRIPT_DIR, "shibuya_3d.html")
with open(output_file, "w") as f:
    f.write(html)

print(f"\nDone! Generated: {output_file}")
print(f"  Buildings: {len(buildings)} (within {RADIUS_M}m)")
print(f"  Roads: {len(roads)}")
print(f"  Railways: {len(railways)} segments")
print(f"  Stations: {len(stations)}")
print(f"  Satellite tiles: {len(gsi_tiles)}")
print(f"  Open in browser: shibuya_3d.html")
