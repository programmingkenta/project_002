"""
Build Photorealistic 3D Shibuya Crossing from PLATEAU LOD2 CityGML data.

This script:
1. Parses PLATEAU CityGML files (LOD2 buildings with textures)
2. Extracts detailed geometry: walls, roofs, architectural features
3. Maps textures to building surfaces
4. Generates photorealistic Three.js WebGL scene (Google Earth quality!)

PLATEAU LOD2 vs previous versions:
  v001/v002: Hand-drawn isometric pixel art
  v003: Simple extruded boxes (LOD1)
  v004: Detailed architecture with real textures (LOD2)

Data source: https://www.geospatial.jp/ckan/dataset/plateau-13113-shibuya-ku-2023
"""

import xml.etree.ElementTree as ET
import math
import json
import os
import base64
import re
from collections import defaultdict

# === CONFIGURATION ===
CROSSING_LAT = 35.6594
CROSSING_LON = 139.7006
RADIUS_M = 200
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

M_PER_DEG_LAT = 111000
M_PER_DEG_LON = 111000 * math.cos(math.radians(CROSSING_LAT))


def latlon_to_meters(lat, lon):
    """Convert lat/lon to meters from crossing center (Three.js coords)."""
    x = (lon - CROSSING_LON) * M_PER_DEG_LON
    z = -(lat - CROSSING_LAT) * M_PER_DEG_LAT
    return x, z


# === STEP 1: PARSE CITYGML FILES ===
print("Step 1: Parsing PLATEAU CityGML files...")

citygml_dir = os.path.join(SCRIPT_DIR, "plateau_data", "udx", "bldg")
appearance_base = os.path.join(SCRIPT_DIR, "plateau_data", "udx", "bldg")

# CityGML namespaces
NS = {
    'core': 'http://www.opengis.net/citygml/2.0',
    'bldg': 'http://www.opengis.net/citygml/building/2.0',
    'gml': 'http://www.opengis.net/gml',
    'app': 'http://www.opengis.net/citygml/appearance/2.0',
    'xlink': 'http://www.w3.org/1999/xlink',
}

def parse_gml_pos_list(pos_list_text):
    """Parse GML posList: 'lat1 lon1 height1 lat2 lon2 height2...' → [(x,y,z)...]."""
    coords = list(map(float, pos_list_text.strip().split()))
    # Group into triplets: (lat, lon, height)
    points = []
    for i in range(0, len(coords), 3):
        if i+2 >= len(coords):
            break
        lat, lon, height = coords[i], coords[i+1], coords[i+2]
        x, z = latlon_to_meters(lat, lon)
        points.append({'x': round(x, 2), 'y': round(height, 2), 'z': round(z, 2)})
    return points


def extract_building_from_gml(building_elem, root, polygon_cache):
    """Extract building geometry and metadata from a bldg:Building element.

    Args:
        building_elem: The bldg:Building XML element
        root: The root of the entire CityGML document (kept for compatibility)
        polygon_cache: Dict mapping polygon IDs to polygon elements (for fast XLink resolution)
    """
    try:
        bldg_id = building_elem.get('{' + NS['gml'] + '}id', '')

        # Quick distance check from first coordinate (for debug)
        qdist = None
        qx, qz = None, None
        quick_pos = building_elem.find('.//gml:posList', NS)
        if quick_pos is not None:
            qcoords = quick_pos.text.strip().split()[:3]
            if len(qcoords) >= 3:
                qlat, qlon = float(qcoords[0]), float(qcoords[1])
                qx, qz = latlon_to_meters(qlat, qlon)
                qdist = math.sqrt(qx**2 + qz**2)
                if qdist < 100:
                    print(f"      >> Parsing building at {qdist:.1f}m from crossing...")

        # Extract basic metadata
        usage_elem = building_elem.find('bldg:usage', NS)
        usage = usage_elem.text if usage_elem is not None else 'unknown'

        # Try to extract height from measuredHeight
        height = 0
        height_elem = building_elem.find('bldg:measuredHeight', NS)
        if height_elem is not None:
            height = float(height_elem.text)

        # Extract LOD2 geometry (detailed building shape)
        # LOD2Solid contains the full 3D building geometry with walls and roofs
        lod_container = building_elem.find('.//bldg:lod2Solid', NS)

        if lod_container is None:
            # Fallback to LOD1 if LOD2 not available
            lod_container = building_elem.find('.//bldg:lod1Solid', NS)

        if lod_container is None:
            if qdist is not None and qdist < 100:
                print(f"    SKIP (no LOD): Building at {qdist:.1f}m has no LOD2/LOD1 geometry")
            return None

        # Get the actual gml:Solid element inside the LOD container
        # Structure: bldg:lodXSolid > gml:Solid > gml:exterior > gml:CompositeSurface > gml:surfaceMember > gml:Polygon
        gml_solid = lod_container.find('gml:Solid', NS)
        if gml_solid is None:
            # Try namespace-agnostic search using iter()
            solid_candidates = [elem for elem in lod_container.iter() if elem.tag.endswith('Solid')]
            gml_solid = solid_candidates[0] if solid_candidates else lod_container

        # Extract all polygons from the solid geometry
        # Each polygon is a surface (wall, roof, ground)
        polygons = []
        first_point_for_debug = None

        # Simplified debug for close buildings
        if qdist is not None and qdist < 100 and gml_solid is not None:
            print(f"    DEBUG: ID={bldg_id[:40]}, LOD={'2' if lod_container.tag.endswith('lod2Solid') else '1'}")

        # Try namespace-aware search first - search from gml_solid, not lod_container
        poly_elems = gml_solid.findall('.//gml:Polygon', NS) if gml_solid is not None else []

        # If no inline polygons found, check for XLink references (LOD2 uses these)
        if not poly_elems and gml_solid is not None:
            # Find all surfaceMembers with xlink:href attributes
            surface_members = gml_solid.findall('.//gml:surfaceMember', NS)
            for sm in surface_members:
                xlink_href = sm.get('{' + NS['xlink'] + '}href', '')
                if xlink_href and xlink_href.startswith('#'):
                    # Resolve the XLink reference using the pre-built cache
                    poly_id = xlink_href[1:]  # Remove the '#' prefix
                    poly_ref = polygon_cache.get(poly_id)
                    if poly_ref is not None:
                        poly_elems.append(poly_ref)

        # Fallback: use iter() to find all Polygon elements regardless of namespace
        if not poly_elems and gml_solid is not None:
            poly_elems = [elem for elem in gml_solid.iter() if elem.tag.endswith('Polygon')]

        if qdist is not None and qdist < 100:
            print(f"    DEBUG: Found {len(poly_elems)} polygons")

        for poly_elem in poly_elems:
            # Get exterior ring (main polygon outline)
            pos_list = poly_elem.find('.//gml:posList', NS)
            if pos_list is None:
                # Try namespace-agnostic search using iter()
                pos_list_candidates = [elem for elem in poly_elem.iter() if elem.tag.endswith('posList')]
                if pos_list_candidates:
                    pos_list = pos_list_candidates[0]

            if pos_list is not None:
                points = parse_gml_pos_list(pos_list.text)
                if len(points) >= 3:
                    if first_point_for_debug is None and points:
                        first_point_for_debug = points[0]
                    polygons.append(points)

        if not polygons:
            if qdist is not None and qdist < 100:
                print(f"    SKIP (no polygons): Building at {qdist:.1f}m has LOD but no valid polygons")
            return None

        # Calculate building center from FIRST polygon only (building footprint)
        # Using all polygons can include far-away geometry like underground parts
        first_poly = polygons[0]
        center_x = sum(p['x'] for p in first_poly) / len(first_poly)
        center_z = sum(p['z'] for p in first_poly) / len(first_poly)

        # Collect all heights for building height calculation
        all_y = [p['y'] for poly in polygons for p in poly]

        # Distance from crossing
        dist = math.sqrt(center_x**2 + center_z**2)

        # Debug: Compare quick distance vs final distance
        if qdist is not None and qdist < 100:  # Was close in quick check
            fp_str = f"quick={qdist:.1f}m, final={dist:.1f}m"
            print(f"    DEBUG MISMATCH: {fp_str}, quick_pt=({qx:.1f},{qz:.1f}), center=({center_x:.1f},{center_z:.1f})")

        # Debug: print buildings that end up close
        if dist < 100:
            fp_str = f"first_pt=({first_point_for_debug['x']:.1f}, {first_point_for_debug['z']:.1f})" if first_point_for_debug else "no_pts"
            print(f"    DEBUG: Found close building! ID={bldg_id[:20]}... dist={dist:.1f}m, center=({center_x:.1f}, {center_z:.1f}), {fp_str}")

        # Use max Y if height not specified
        if height == 0 and all_y:
            height = max(all_y)

        return {
            'id': bldg_id,
            'usage': usage,
            'height': height,
            'center_x': round(center_x, 2),
            'center_z': round(center_z, 2),
            'distance': round(dist, 1),
            'polygons': polygons,  # List of 3D polygons (walls, roofs, etc.)
            'within_radius': dist <= RADIUS_M,  # Flag for filtering
        }
    except Exception as e:
        # Print exceptions for buildings that were close in quick check
        if qdist is not None and qdist < 100:
            print(f"    ERROR parsing close building ({qdist:.1f}m): {type(e).__name__}: {e}")
        return None


# Parse all CityGML files in the directory
buildings = []
gml_files = [f for f in os.listdir(citygml_dir) if f.endswith('.gml')]

print(f"  Found {len(gml_files)} CityGML files to parse")

for gml_file in gml_files:  # Parse all files to find crossing area
    gml_path = os.path.join(citygml_dir, gml_file)
    print(f"  Parsing {gml_file}...")

    try:
        tree = ET.parse(gml_path)
        root = tree.getroot()

        # Build polygon cache for fast XLink resolution (LOD2 uses XLinks)
        # This pre-indexes all polygons by their gml:id attribute
        polygon_cache = {}
        for poly in root.iter():
            if poly.tag.endswith('Polygon'):
                poly_id = poly.get('{' + NS['gml'] + '}id')
                if poly_id:
                    polygon_cache[poly_id] = poly

        file_count = 0
        for bldg_elem in root.findall('.//bldg:Building', NS):
            building = extract_building_from_gml(bldg_elem, root, polygon_cache)
            if building:
                buildings.append(building)
                file_count += 1
        print(f"    -> Extracted {file_count} buildings from this file")
    except Exception as e:
        print(f"    Warning: Error parsing {gml_file}: {e}")
        continue

# Filter to only buildings within radius
print(f"  Total buildings parsed: {len(buildings)}")

# Debug: show distance distribution
if buildings:
    distances = [b['distance'] for b in buildings]
    print(f"  Distance range: {min(distances):.1f}m - {max(distances):.1f}m")
    within = [b for b in buildings if b.get('within_radius', False)]
    print(f"  Buildings with within_radius=True: {len(within)}")

    # Show a few closest
    sorted_b = sorted(buildings, key=lambda x: x['distance'])
    print(f"  Closest buildings:")
    for b in sorted_b[:5]:
        print(f"    {b['distance']:.1f}m - within_radius={b.get('within_radius', 'MISSING')}")

buildings = [b for b in buildings if b.get('within_radius', False)]
print(f"  Final count within {RADIUS_M}m: {len(buildings)}")

# Show statistics
if buildings:
    heights = [b['height'] for b in buildings if b['height'] > 0]
    if heights:
        print(f"  Height range: {min(heights):.0f}m – {max(heights):.0f}m")

    poly_counts = [len(b['polygons']) for b in buildings]
    print(f"  Polygon count per building: {min(poly_counts)} – {max(poly_counts)}")
    print(f"  Total polygons: {sum(poly_counts)}")


# === STEP 2: MATCH BUILDING NAMES FROM OSM ===
print("Step 2: Matching building names from OSM...")

osm_file = "/home/kenta/Downloads/Shibuya Crossing Map.osm"
osm_tree = ET.parse(osm_file)
osm_root = osm_tree.getroot()

osm_nodes = {}
for node in osm_root.findall("node"):
    node_id = node.get("id")
    lat = float(node.get("lat"))
    lon = float(node.get("lon"))
    osm_nodes[node_id] = {"lat": lat, "lon": lon}

osm_named_buildings = []
for way in osm_root.findall("way"):
    tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
    if "building" not in tags:
        continue
    name = tags.get("name:en") or tags.get("name") or ""
    if not name:
        continue

    node_refs = [nd.get("ref") for nd in way.findall("nd")]
    coords = [osm_nodes[ref] for ref in node_refs if ref in osm_nodes]
    if len(coords) < 3:
        continue

    center_lat = sum(c["lat"] for c in coords) / len(coords)
    center_lon = sum(c["lon"] for c in coords) / len(coords)
    osm_named_buildings.append({"name": name, "lat": center_lat, "lon": center_lon})

# Match OSM names to CityGML buildings
for osm_b in osm_named_buildings:
    ox, oz = latlon_to_meters(osm_b["lat"], osm_b["lon"])
    best_dist = 999999
    best_match = None
    for pb in buildings:
        dx = ox - pb["center_x"]
        dz = oz - pb["center_z"]
        d = math.sqrt(dx**2 + dz**2)
        if d < best_dist:
            best_dist = d
            best_match = pb
    if best_match and best_dist < 30:
        best_match["name"] = osm_b["name"]

named = [b for b in buildings if "name" in b]
print(f"  Matched {len(named)} building names:")
for b in named[:10]:
    print(f"    - {b['name']} ({b['height']:.0f}m, {len(b['polygons'])} surfaces)")

# Filter out Shibuya Scramble Square
original_count = len(buildings)
buildings = [b for b in buildings if not (
    'name' in b and ('Scramble Square' in b['name'] or 'スクランブルスクエア' in b['name'])
)]
removed_count = original_count - len(buildings)
if removed_count > 0:
    print(f"  Removed {removed_count} building(s): Shibuya Scramble Square")


# === STEP 3: LOAD RAILWAYS & STATIONS ===
# === STEP 2.5: LOAD OSM ROADS ===
print("Step 2.5: Loading road data from OpenStreetMap...")

osm_roads_path = os.path.join(SCRIPT_DIR, "plateau_data", "osm_roads.json")
roads = []

try:
    with open(osm_roads_path, 'r', encoding='utf-8') as f:
        osm_roads_data = json.load(f)

    # Build node lookup
    nodes = {}
    for elem in osm_roads_data['elements']:
        if elem['type'] == 'node':
            nodes[elem['id']] = {'lat': elem['lat'], 'lon': elem['lon']}

    # Process ways
    for elem in osm_roads_data['elements']:
        if elem['type'] != 'way':
            continue

        tags = elem.get('tags', {})
        highway_type = tags.get('highway', '')
        name = tags.get('name', tags.get('name:en', ''))

        # Get node coordinates
        node_ids = elem.get('nodes', [])
        if len(node_ids) < 2:
            continue

        points = []
        for nid in node_ids:
            if nid in nodes:
                lat = nodes[nid]['lat']
                lon = nodes[nid]['lon']
                x, z = latlon_to_meters(lat, lon)
                points.append({'x': round(x, 2), 'y': 0, 'z': round(z, 2)})

        if len(points) >= 2:
            # Determine road width based on type
            width = {
                'motorway': 12,
                'trunk': 10,
                'primary': 8,
                'secondary': 7,
                'tertiary': 6,
                'residential': 5,
                'unclassified': 4
            }.get(highway_type, 4)

            roads.append({
                'name': name,
                'highway': highway_type,
                'width': width,
                'points': points
            })

    print(f"  Loaded {len(roads)} roads")
    named_roads = [r for r in roads if r['name']]
    if named_roads:
        print(f"  Named roads: {len(named_roads)}")
        for r in named_roads[:5]:
            print(f"    - {r['name']} ({r['highway']}, {len(r['points'])} points)")
except Exception as e:
    print(f"  Warning: Could not load roads: {e}")

print("Step 3: Loading railway data...")

railway_path = os.path.join(SCRIPT_DIR, "plateau_data", "shibuya_related",
                            "13113_shibuya-ku_pref_2023_railway.geojson")
station_path = os.path.join(SCRIPT_DIR, "plateau_data", "shibuya_related",
                            "13113_shibuya-ku_pref_2023_station.geojson")

LINE_COLORS = {
    "山手線": "#80C241", "中央線": "#F15A22", "井の頭線": "#9B7CB6",
    "京王線": "#DD0033", "小田原線": "#1E72B7", "田園都市線": "#009944",
    "東横線": "#E5171F", "3号線銀座線": "#F39700", "11号線半蔵門線": "#8F76D6",
    "13号線副都心線": "#9C5E31", "9号線千代田線": "#00A650", "2号線日比谷線": "#B5B5AC",
    "10号線新宿線": "#6CBB5A", "12号線大江戸線": "#B6007A",
}

railways = []
stations = []

if os.path.exists(railway_path):
    with open(railway_path) as f:
        railway_geojson = json.load(f)

    for feature in railway_geojson["features"]:
        line_name = feature["properties"].get("路線名", "")
        color = LINE_COLORS.get(line_name, "#888888")

        for line_coords in feature["geometry"]["coordinates"]:
            coords_m = []
            for pt in line_coords:
                mx, mz = latlon_to_meters(pt[1], pt[0])
                coords_m.append({"x": round(mx, 2), "z": round(mz, 2)})
            if len(coords_m) >= 2:
                railways.append({"name": line_name, "color": color, "coords": coords_m})

    print(f"  Loaded {len(railways)} railway segments")

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
        stations.append({"name": name, "line": line, "color": color,
                        "x": round(mx, 2), "z": round(mz, 2)})

    print(f"  Loaded {len(stations)} stations")


# === STEP 4: SERIALIZE TO JSON ===
print("Step 4: Serializing geometry...")

buildings_json = json.dumps(buildings)
roads_json = json.dumps(roads)
railways_json = json.dumps(railways)
stations_json = json.dumps(stations)

legend_lines = {}
for r in railways:
    if r["name"] not in legend_lines:
        legend_lines[r["name"]] = r["color"]
legend_json = json.dumps(legend_lines)


# === STEP 5: GENERATE HTML WITH THREE.JS ===
print("Step 5: Generating photorealistic 3D HTML...")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Photorealistic Shibuya Crossing — PLATEAU LOD2</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ overflow: hidden; background: #0a0a1a; font-family: monospace; }}
        canvas {{ display: block; }}

        #hud {{
            position: fixed;
            top: 16px;
            left: 16px;
            color: #ff7799;
            font-size: 16px;
            z-index: 10;
            letter-spacing: 2px;
        }}
        #stats {{
            position: fixed;
            top: 50px;
            left: 16px;
            color: #556;
            font-size: 11px;
            z-index: 10;
        }}
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
            display: none;
            backdrop-filter: blur(8px);
            z-index: 10;
        }}
        #info-panel .title {{ color: #ff7799; font-size: 16px; font-weight: bold; margin-bottom: 8px; }}
        #info-panel .row {{ display: flex; justify-content: space-between; padding: 3px 0; }}
        #info-panel .label {{ color: #888; }}
        #info-panel .value {{ color: #eee; }}
        #info-panel .close {{ position: absolute; top: 8px; right: 12px; color: #666; cursor: pointer; }}
        #info-panel .close:hover {{ color: #ff7799; }}
    </style>
</head>
<body>
    <div id="hud">SHIBUYA CROSSING — PLATEAU LOD2</div>
    <div id="stats">Loading geometry...</div>

    <div id="info-panel">
        <span class="close" onclick="document.getElementById('info-panel').style.display='none'">&times;</span>
        <div class="title" id="info-title">Building</div>
        <div id="info-rows"></div>
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

        // === DATA FROM PLATEAU LOD2 ===
        const buildings = {buildings_json};
        const roads = {roads_json};
        const railways = {railways_json};
        const stations = {stations_json};

        document.getElementById('stats').textContent =
            `${{buildings.length}} LOD2 buildings · ${{buildings.reduce((s,b)=>s+b.polygons.length,0)}} surfaces · ${{roads.length}} roads`;

        // === SCENE SETUP ===
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87CEEB);  // Sky blue
        scene.fog = new THREE.FogExp2(0xCCDDFF, 0.001);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.5, 2000);
        camera.position.set(180, 180, 260);

        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.1;
        document.body.appendChild(renderer.domElement);

        // === REALISTIC LIGHTING (mimics sunlight) ===
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xfff5e6, 1.5);
        sunLight.position.set(100, 250, 150);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 4096;
        sunLight.shadow.mapSize.height = 4096;
        sunLight.shadow.camera.left = -300;
        sunLight.shadow.camera.right = 300;
        sunLight.shadow.camera.top = 300;
        sunLight.shadow.camera.bottom = -300;
        sunLight.shadow.camera.near = 1;
        sunLight.shadow.camera.far = 700;
        sunLight.shadow.bias = -0.0005;
        scene.add(sunLight);

        // Sky hemisphere light (blue from above, earth tone from below)
        const hemiLight = new THREE.HemisphereLight(0xB0C4DE, 0xD2B48C, 0.4);
        scene.add(hemiLight);

        // === CAMERA CONTROLS ===
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 30, 0);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.maxPolarAngle = Math.PI / 2 - 0.02;
        controls.minDistance = 30;
        controls.maxDistance = 800;
        controls.update();

        // === GROUND ===
        const groundGeo = new THREE.PlaneGeometry(800, 800);
        const groundMat = new THREE.MeshStandardMaterial({{
            color: 0x556B2F,
            roughness: 0.9,
            metalness: 0.0,
        }});
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.1;
        ground.receiveShadow = true;
        scene.add(ground);

        // === RENDER LOD2 BUILDINGS ===
        const buildingMeshes = [];

        for (const b of buildings) {{
            if (!b.polygons || b.polygons.length === 0) continue;

            // Create a THREE.Group to hold all surfaces of this building
            const buildingGroup = new THREE.Group();
            buildingGroup.userData = b;

            // Each polygon is a surface (wall, roof, ground, etc.)
            for (const poly of b.polygons) {{
                if (poly.length < 3) continue;

                // Convert polygon points to THREE.js vectors
                const vertices = [];
                for (const pt of poly) {{
                    vertices.push(new THREE.Vector3(pt.x, pt.y, pt.z));
                }}

                // Create a flat shape from the vertices
                // Note: CityGML polygons are already in 3D space, so we use BufferGeometry
                const positions = [];
                for (let i = 1; i < vertices.length - 1; i++) {{
                    // Triangle fan: v0, v1, v2, then v0, v2, v3, etc.
                    positions.push(vertices[0].x, vertices[0].y, vertices[0].z);
                    positions.push(vertices[i].x, vertices[i].y, vertices[i].z);
                    positions.push(vertices[i+1].x, vertices[i+1].y, vertices[i+1].z);
                }}

                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position',
                    new THREE.Float32BufferAttribute(positions, 3));
                geometry.computeVertexNormals();

                // Material: realistic concrete/glass based on surface orientation
                // TODO(human): Design materials based on surface type (wall vs roof)!
                //
                // You can detect if a surface is:
                //   - Roof: normal vector points mostly upward (normal.y > 0.7)
                //   - Wall: normal vector is mostly horizontal (abs(normal.y) < 0.7)
                //   - Ground: normal vector points mostly downward (normal.y < -0.7)
                //
                // Ideas:
                //   - Roofs: dark gray tiles, high roughness (0.9)
                //   - Walls: light concrete or glass, medium roughness (0.3-0.6)
                //   - Tall buildings: more glass-like (lower roughness, slight metalness)
                //
                // Hint: geometry.getAttribute('normal').array contains normal vectors

                const material = new THREE.MeshStandardMaterial({{
                    color: 0xDDDDDD,
                    roughness: 0.7,
                    metalness: 0.1,
                    side: THREE.DoubleSide,
                }});

                const mesh = new THREE.Mesh(geometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                buildingGroup.add(mesh);
            }}

            scene.add(buildingGroup);
            buildingMeshes.push(buildingGroup);
        }}

        console.log(`Rendered ${{buildingMeshes.length}} LOD2 buildings with ${{buildings.reduce((s,b)=>s+b.polygons.length,0)}} surfaces`);

        // === BUILDING LABELS ===
        for (const b of buildings) {{
            if (!b.name) continue;
            const canvas2d = document.createElement('canvas');
            const ctx2d = canvas2d.getContext('2d');
            canvas2d.width = 512;
            canvas2d.height = 64;
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
            sprite.position.set(b.center_x, b.height + 15, b.center_z);
            sprite.scale.set(45, 5.625, 1);
            scene.add(sprite);
        }}

        // === ROADS ===
        console.log(`Rendering ${{roads.length}} roads...`);
        for (const road of roads) {{
            if (road.points.length < 2) continue;

            // Create road geometry as extruded path (raised 0.5m above ground)
            const roadPoints = road.points.map(p => new THREE.Vector3(p.x, 0.5, p.z));

            // Create road surface as flat ribbons
            const width = road.width / 2;  // Half-width for each side
            const geometry = new THREE.BufferGeometry();
            const positions = [];
            const indices = [];

            for (let i = 0; i < roadPoints.length; i++) {{
                const p = roadPoints[i];

                // Calculate perpendicular direction
                let dir;
                if (i < roadPoints.length - 1) {{
                    dir = new THREE.Vector3().subVectors(roadPoints[i + 1], p).normalize();
                }} else {{
                    dir = new THREE.Vector3().subVectors(p, roadPoints[i - 1]).normalize();
                }}

                const perp = new THREE.Vector3(-dir.z, 0, dir.x);
                const left = new THREE.Vector3().addVectors(p, perp.clone().multiplyScalar(width));
                const right = new THREE.Vector3().addVectors(p, perp.clone().multiplyScalar(-width));

                positions.push(left.x, left.y, left.z);
                positions.push(right.x, right.y, right.z);

                if (i < roadPoints.length - 1) {{
                    const idx = i * 2;
                    indices.push(idx, idx + 1, idx + 2);
                    indices.push(idx + 1, idx + 3, idx + 2);
                }}
            }}

            geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
            geometry.setIndex(indices);
            geometry.computeVertexNormals();

            // Road material: lighter gray asphalt for better visibility
            const material = new THREE.MeshStandardMaterial({{
                color: 0x555555,
                roughness: 0.8,
                metalness: 0.0,
            }});

            const mesh = new THREE.Mesh(geometry, material);
            mesh.receiveShadow = true;
            mesh.castShadow = true;
            scene.add(mesh);

            // Add road edges (white lines) for major roads
            if (road.width >= 6) {{
                const edgeMaterial = new THREE.LineBasicMaterial({{
                    color: 0xFFFFFF,
                    linewidth: 2,
                    opacity: 0.6,
                    transparent: true
                }});

                const leftEdgePoints = [];
                const rightEdgePoints = [];

                for (let i = 0; i < roadPoints.length; i++) {{
                    const p = roadPoints[i];
                    let dir;
                    if (i < roadPoints.length - 1) {{
                        dir = new THREE.Vector3().subVectors(roadPoints[i + 1], p).normalize();
                    }} else {{
                        dir = new THREE.Vector3().subVectors(p, roadPoints[i - 1]).normalize();
                    }}
                    const perp = new THREE.Vector3(-dir.z, 0, dir.x);
                    leftEdgePoints.push(new THREE.Vector3().addVectors(p, perp.clone().multiplyScalar(width)));
                    rightEdgePoints.push(new THREE.Vector3().addVectors(p, perp.clone().multiplyScalar(-width)));
                }}

                const leftEdgeGeometry = new THREE.BufferGeometry().setFromPoints(leftEdgePoints);
                const leftEdgeLine = new THREE.Line(leftEdgeGeometry, edgeMaterial);
                scene.add(leftEdgeLine);

                const rightEdgeGeometry = new THREE.BufferGeometry().setFromPoints(rightEdgePoints);
                const rightEdgeLine = new THREE.Line(rightEdgeGeometry, edgeMaterial);
                scene.add(rightEdgeLine);
            }}
        }}
        console.log(`Roads rendered!`);

        // === RAILWAY LINES ===
        for (const rail of railways) {{
            if (rail.coords.length < 2) continue;
            const positions = [];
            for (const pt of rail.coords) {{
                positions.push(pt.x, 8, pt.z);  // Elevated at 8m
            }}

            const geo = new LineGeometry();
            geo.setPositions(positions);
            const mat = new LineMaterial({{
                color: new THREE.Color(rail.color).getHex(),
                linewidth: 2,
                resolution: new THREE.Vector2(window.innerWidth, window.innerHeight),
            }});
            scene.add(new Line2(geo, mat));
        }}

        // === STATIONS ===
        for (const station of stations) {{
            const sphereGeo = new THREE.SphereGeometry(4, 16, 12);
            const sphereMat = new THREE.MeshStandardMaterial({{
                color: new THREE.Color(station.color),
                emissive: new THREE.Color(station.color),
                emissiveIntensity: 0.5,
                roughness: 0.3,
                metalness: 0.6,
            }});
            const sphere = new THREE.Mesh(sphereGeo, sphereMat);
            sphere.position.set(station.x, 12, station.z);
            scene.add(sphere);
        }}

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
            if (Math.sqrt(dx*dx + dy*dy) > 5) return;

            mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const hits = raycaster.intersectObjects(buildingMeshes, true);

            if (hits.length > 0) {{
                // Find the building group
                let group = hits[0].object;
                while (group.parent && !group.userData.id) {{
                    group = group.parent;
                }}
                if (group.userData.id) {{
                    showBuildingInfo(group.userData);
                }}
            }} else {{
                document.getElementById('info-panel').style.display = 'none';
            }}
        }});

        function showBuildingInfo(b) {{
            const panel = document.getElementById('info-panel');
            document.getElementById('info-title').textContent = b.name || 'Building';

            const rows = [
                ['Height', b.height.toFixed(1) + 'm'],
                ['Surfaces', b.polygons.length],
                ['Distance', b.distance + 'm'],
                ['ID', b.id.replace('bldg_', '').slice(0, 16) + '...'],
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

        console.log('Photorealistic Shibuya Crossing loaded — PLATEAU LOD2');
    </script>
</body>
</html>"""

output_file = os.path.join(SCRIPT_DIR, "shibuya_lod2.html")
with open(output_file, "w") as f:
    f.write(html)

print(f"\nDone! Generated: {output_file}")
print(f"  Buildings: {len(buildings)} LOD2 models")
print(f"  Total surfaces: {sum(len(b['polygons']) for b in buildings)}")
print(f"  Roads: {len(roads)} from OpenStreetMap")
print(f"  Railways: {len(railways)} segments")
print(f"  Stations: {len(stations)}")
print(f"\nOpen in browser: shibuya_lod2.html")
print("\nNote: This uses real PLATEAU geometry!")
print("      For textures, we'll add appearance parsing in the next iteration.")
