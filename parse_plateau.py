"""Parse PLATEAU CityGML building data near Shibuya Crossing.

Uses iterparse (streaming XML) because the GML files are 30-100MB each.
Extracts: building footprints, heights, floors, usage codes.
"""

import xml.etree.ElementTree as ET
import json
import math
import os

# === NAMESPACES ===
# CityGML uses XML namespaces heavily. We need these to find elements.
NS = {
    "core": "http://www.opengis.net/citygml/2.0",
    "bldg": "http://www.opengis.net/citygml/building/2.0",
    "gml":  "http://www.opengis.net/gml",
    "gen":  "http://www.opengis.net/citygml/generics/2.0",
}

# === TARGET AREA ===
# Shibuya Crossing center
CENTER_LAT = 35.6591
CENTER_LON = 139.7005
RADIUS_M = 350  # meters from crossing center

def haversine(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points."""
    R = 6371000  # Earth radius in meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def parse_poslist(text):
    """Parse a GML posList string into [(lat, lon, z), ...] tuples."""
    nums = text.strip().split()
    points = []
    for i in range(0, len(nums) - 2, 3):
        lat = float(nums[i])
        lon = float(nums[i + 1])
        z = float(nums[i + 2])
        points.append((lat, lon, z))
    return points

def centroid(points):
    """Average lat/lon of a list of points."""
    if not points:
        return 0, 0
    avg_lat = sum(p[0] for p in points) / len(points)
    avg_lon = sum(p[1] for p in points) / len(points)
    return avg_lat, avg_lon

def parse_building(elem):
    """Extract data from one <bldg:Building> element."""
    building = {}

    # Height
    h = elem.find(".//bldg:measuredHeight", NS)
    if h is not None and h.text:
        building["height"] = float(h.text)

    # Floors
    floors = elem.find(".//bldg:storeysAboveGround", NS)
    if floors is not None and floors.text:
        building["floors"] = int(floors.text)

    basement = elem.find(".//bldg:storeysBelowGround", NS)
    if basement is not None and basement.text:
        building["basement_floors"] = int(basement.text)

    # Usage code
    usage = elem.find(".//bldg:usage", NS)
    if usage is not None and usage.text:
        building["usage_code"] = usage.text

    # Roof outline (lod0RoofEdge) — the footprint polygon
    roof_edge = elem.find(".//bldg:lod0RoofEdge//gml:posList", NS)
    if roof_edge is not None and roof_edge.text:
        points = parse_poslist(roof_edge.text)
        building["footprint"] = [(p[0], p[1]) for p in points]

        # Calculate center and check distance
        clat, clon = centroid(points)
        building["center_lat"] = clat
        building["center_lon"] = clon
        building["ground_elevation"] = points[0][2] if points else 0

    # Building ID
    gml_id = elem.get("{http://www.opengis.net/gml}id")
    if gml_id:
        building["id"] = gml_id

    return building

def parse_gml_file(filepath):
    """Stream-parse a CityGML file and extract buildings near the crossing."""
    buildings = []
    count = 0
    skipped = 0

    print(f"Parsing {os.path.basename(filepath)}...")

    # iterparse streams through XML without loading it all into memory
    for event, elem in ET.iterparse(filepath, events=("end",)):
        if elem.tag == "{http://www.opengis.net/citygml/building/2.0}Building":
            count += 1
            building = parse_building(elem)

            # Filter: must have height and center
            if "height" in building and "center_lat" in building:
                dist = haversine(
                    CENTER_LAT, CENTER_LON,
                    building["center_lat"], building["center_lon"]
                )
                building["distance_from_crossing"] = round(dist, 1)

                if dist <= RADIUS_M:
                    buildings.append(building)
                else:
                    skipped += 1
            else:
                skipped += 1

            # Free memory (important for large files!)
            elem.clear()

            if count % 500 == 0:
                print(f"  ...processed {count} buildings, kept {len(buildings)}")

    print(f"Done! {count} total, {len(buildings)} near crossing, {skipped} skipped")
    return buildings


# === MAIN ===
if __name__ == "__main__":
    data_dir = os.path.dirname(os.path.abspath(__file__))
    gml_dir = os.path.join(data_dir, "plateau_data", "udx", "bldg")

    # Parse the tile covering Shibuya Crossing
    all_buildings = []

    # Main tile (53393596) + adjacent tiles that might have buildings near crossing
    tiles = ["53393596", "53393595"]

    for tile in tiles:
        filepath = os.path.join(gml_dir, f"{tile}_bldg_6697_op.gml")
        if os.path.exists(filepath):
            buildings = parse_gml_file(filepath)
            all_buildings.extend(buildings)
        else:
            print(f"Tile {tile} not extracted yet, skipping...")

    # Sort by distance from crossing
    all_buildings.sort(key=lambda b: b.get("distance_from_crossing", 9999))

    # Save to JSON
    output_path = os.path.join(data_dir, "plateau_data", "shibuya_crossing_buildings.json")
    with open(output_path, "w") as f:
        json.dump(all_buildings, f, indent=2)

    print(f"\nSaved {len(all_buildings)} buildings to {output_path}")
    print(f"\nClosest buildings to Shibuya Crossing:")
    for b in all_buildings[:15]:
        floors_str = f"{b.get('floors', '?')}F" if 'floors' in b else ""
        print(f"  {b.get('distance_from_crossing', '?')}m - {b.get('height', '?')}m tall {floors_str} (usage: {b.get('usage_code', '?')})")
