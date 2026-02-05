"""
Fetch road data from OpenStreetMap around Shibuya Crossing.
"""
import requests
import json

CROSSING_LAT = 35.6594
CROSSING_LON = 139.7006
RADIUS_M = 200

# Calculate bounding box (roughly)
lat_offset = RADIUS_M / 111000  # ~1 degree latitude = 111km
lon_offset = RADIUS_M / (111000 * 0.773)  # adjusted for Tokyo latitude

bbox = {
    'south': CROSSING_LAT - lat_offset,
    'north': CROSSING_LAT + lat_offset,
    'west': CROSSING_LON - lon_offset,
    'east': CROSSING_LON + lon_offset
}

# Overpass API query for roads
overpass_query = f"""
[out:json][timeout:25];
(
  way["highway"]["highway"!~"footway|path|steps|cycleway|service|track"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
);
out body;
>;
out skel qt;
"""

print("Querying OpenStreetMap for roads around Shibuya Crossing...")
print(f"Bounding box: {bbox}")

try:
    response = requests.post(
        'https://overpass-api.de/api/interpreter',
        data=overpass_query,
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    
    print(f"Retrieved {len([e for e in data['elements'] if e['type'] == 'way'])} ways")
    print(f"Retrieved {len([e for e in data['elements'] if e['type'] == 'node'])} nodes")
    
    # Save to file
    with open('plateau_data/osm_roads.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✓ Saved to plateau_data/osm_roads.json")
    
    # Show some road names
    ways = [e for e in data['elements'] if e['type'] == 'way']
    named_roads = [w for w in ways if 'tags' in w and 'name' in w['tags']]
    print(f"\nFound {len(named_roads)} named roads:")
    for w in named_roads[:10]:
        name = w['tags'].get('name', 'unnamed')
        highway = w['tags'].get('highway', 'unknown')
        print(f"  - {name} ({highway})")
    
except Exception as e:
    print(f"Error: {e}")
