# Shibuya 3D Geospatial Visualization

A photorealistic 3D visualization of Shibuya Crossing using PLATEAU LOD2 CityGML data and OpenStreetMap, demonstrating advanced geospatial data engineering and real-time 3D rendering techniques.

## Project Overview

This project processes high-resolution Japanese government geospatial data (PLATEAU) to create an interactive WebGL visualization of Tokyo's busiest intersection. The implementation solves real-world data engineering challenges including XLink reference resolution, coordinate system transformations, and memory-efficient geometry processing.

## Features

- **High-detail building geometry**: PLATEAU LOD2 (Level of Detail 2) with detailed roof structures
- **Road network integration**: OpenStreetMap data via Overpass API
- **Interactive 3D rendering**: Three.js WebGL with orbit controls
- **PBR materials**: Physically-based rendering with proper lighting and shadows
- **Optimized spatial filtering**: 151 buildings within 200m radius using distance calculations
- **Efficient XLink resolution**: O(1) polygon lookup with pre-built cache for large CityGML files

### Live Demo

Open [shibuya_lod2.html](shibuya_lod2.html) in a web browser to view the interactive 3D visualization.

**Project Statistics:**
- 151 buildings with detailed LOD2 geometry
- 6,299 building surfaces (walls, roofs, detailed structures)
- 142 roads including major streets (道玄坂, 玉川通り, 渋谷センター街)
- Real-world coordinate transformation from JGD2011 to local space
- XLink reference resolution for memory-efficient geometry loading

## Data Sources

- **Building data**: [PLATEAU](https://www.mlit.go.jp/plateau/) CityGML LOD2 (Tokyo 13113 mesh)
- **Road data**: [OpenStreetMap](https://www.openstreetmap.org/) via Overpass API

## Key Technical Challenges Solved

### 1. XLink Reference Resolution
**Problem:** PLATEAU LOD2 uses `xlink:href="#poly-xxx"` references instead of inline polygons
**Solution:** Pre-built polygon cache for O(1) lookups instead of O(n²) document searches
**Impact:** Enables processing of large CityGML files with thousands of polygon references

### 2. Coordinate System Transformation
**Problem:** Input data in JGD2011 / Japan Plane Rectangular CS IX (EPSG:6677)
**Solution:** Equirectangular projection converting lat/lon to local meters centered at Shibuya Crossing
**Impact:** Accurate spatial relationships in 3D scene

### 3. Road Visibility in 3D Scene
**Problem:** Roads initially invisible due to z-fighting with ground plane
**Solution:** Elevated roads 0.5m above ground, increased contrast (0x555555), added white edge lines
**Impact:** Clear road network visualization without geometry conflicts

### 4. Memory-Efficient Geometry Loading
**Problem:** 600+ MB PLATEAU data files exceed GitHub limits
**Solution:** Parse and extract only relevant geometry, serialize to compact JSON
**Impact:** Repository stays under GitHub limits while preserving full detail

## Scripts

### Main Visualization Pipeline

**`build_shibuya_map_004.py`** - Production version with all features:
1. Parses PLATEAU CityGML files with XLink reference resolution
2. Extracts LOD2 building geometry within 200m of Shibuya Crossing (35.6595°N, 139.7004°E)
3. Loads OpenStreetMap road data from JSON cache
4. Generates interactive Three.js WebGL visualization

```bash
python build_shibuya_map_004.py
# Output: shibuya_lod2.html
```

**`fetch_osm_roads.py`** - Data fetching utility:
- Queries OpenStreetMap Overpass API for road network
- Filters by highway type (excludes footways, paths, etc.)
- Caches results to `plateau_data/osm_roads.json`

```bash
python fetch_osm_roads.py
# Output: plateau_data/osm_roads.json
```

### Development Iterations

The project evolved through multiple iterations, each addressing specific technical challenges:

- **`build_shibuya_map_001.py`** - Initial CityGML XML parsing
- **`build_shibuya_map_002.py`** - OSM data integration with isometric projection
- **`build_shibuya_map_003.py`** - PLATEAU LOD1 data processing
- **`build_shibuya_map_004.py`** - Production version with LOD2, XLink resolution, and road network

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

## Skills Demonstrated

### Python Programming
- XML parsing with ElementTree
- Coordinate system transformations
- Spatial data filtering and queries
- Algorithm optimization (O(n²) → O(n))
- JSON serialization and data caching

### Geospatial Data Engineering
- PLATEAU CityGML LOD2 parsing
- XLink reference resolution
- OpenStreetMap Overpass API integration
- Coordinate system transformations (EPSG:6677 → local)
- Spatial filtering by distance

### 3D Visualization
- Three.js WebGL scene setup
- PBR material creation
- Geometry construction from real-world data
- Z-fighting prevention techniques
- Interactive camera controls

### Software Engineering
- Iterative development (v001 → v004)
- Code documentation and comments
- Performance optimization
- Error handling and debugging
- Version control with Git

## Requirements

- Python 3.x
- Standard library only (xml.etree.ElementTree, json, math, urllib)
- Modern web browser with WebGL support
- No external Python dependencies required

## License

This project uses open data:
- PLATEAU data: [PLATEAU Policy](https://www.mlit.go.jp/plateau/site-policy/)
- OpenStreetMap data: [ODbL](https://www.openstreetmap.org/copyright)

## Acknowledgments

- **PLATEAU** by Ministry of Land, Infrastructure, Transport and Tourism (MLIT) - High-quality 3D city models
- **OpenStreetMap contributors** - Comprehensive road network data
- **Three.js** - Powerful WebGL rendering library
- **Claude Code** - AI pair programming for learning and debugging

---

**High-fidelity 3D visualization from government geospatial data.** This project demonstrates production-ready data engineering techniques for processing CityGML LOD2 data and rendering complex urban environments in real-time.
