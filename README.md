# Shibuya 3D Map Visualization

A photorealistic 3D visualization of Shibuya Crossing using PLATEAU LOD2 CityGML building data and OpenStreetMap road network data, rendered with Three.js.

## Features

- **High-detail building geometry**: Uses PLATEAU LOD2 (Level of Detail 2) building data with detailed roof structures
- **Road network**: Integrates OpenStreetMap road data for accurate street layouts
- **Interactive 3D view**: Navigate the scene with mouse controls (orbit, zoom, pan)
- **Realistic rendering**: PBR materials with proper lighting and shadows
- **Spatial filtering**: Extracts buildings within 200m radius of Shibuya Crossing

## Demo

Open `shibuya_lod2.html` in a web browser to view the 3D visualization.

**Statistics:**
- 151 buildings with detailed geometry
- 6,299 building surfaces
- 142 roads including major streets (道玄坂, 玉川通り, 渋谷センター街)

## Data Sources

- **Building data**: [PLATEAU](https://www.mlit.go.jp/plateau/) CityGML LOD2 (Tokyo 13113 mesh)
- **Road data**: [OpenStreetMap](https://www.openstreetmap.org/) via Overpass API

## Scripts

### `build_shibuya_map_004.py`
Main script that:
1. Parses PLATEAU CityGML files with XLink reference resolution
2. Extracts LOD2 building geometry within 200m of Shibuya Crossing (35.6595°N, 139.7004°E)
3. Loads OpenStreetMap road data
4. Generates a Three.js WebGL visualization in `shibuya_lod2.html`

```bash
python build_shibuya_map_004.py
```

### `fetch_osm_roads.py`
Fetches road network data from OpenStreetMap Overpass API for the Shibuya Crossing area.

```bash
python fetch_osm_roads.py
```

## Technical Details

### XLink Resolution
PLATEAU LOD2 data uses XLink references (`xlink:href="#poly-xxx"`) instead of inline polygons for file size optimization. The script builds a polygon cache for O(1) lookup performance.

### Coordinate System
- Input: JGD2011 / Japan Plane Rectangular CS IX (EPSG:6677)
- Output: Local coordinates centered at Shibuya Crossing
- Buildings filtered by distance calculation from center point

### Road Rendering
- Roads elevated 0.5m above ground to prevent z-fighting
- Major roads (≥6m width) include white edge lines for lane markings
- Color hierarchy based on road type (motorway, trunk, primary, etc.)

## Requirements

- Python 3.x
- Standard library only (xml.etree.ElementTree, json, math, urllib)
- Modern web browser with WebGL support

## License

This project uses open data:
- PLATEAU data: [PLATEAU Policy](https://www.mlit.go.jp/plateau/site-policy/)
- OpenStreetMap data: [ODbL](https://www.openstreetmap.org/copyright)

## Acknowledgments

- PLATEAU by Ministry of Land, Infrastructure, Transport and Tourism (MLIT)
- OpenStreetMap contributors
- Three.js library
