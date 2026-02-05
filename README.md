# Python Learning Journey: From Hello World to 3D Geospatial Visualization

A portfolio repository documenting progression from Python fundamentals to advanced geospatial data processing and 3D visualization. The culminating project is a photorealistic 3D model of Shibuya Crossing using government open data (PLATEAU) and OpenStreetMap.

## Repository Overview

This repository contains:
1. **Learning Tutorials** - Foundational Python concepts with hands-on exercises
2. **Progressive Projects** - City builder exercises building up to real-world mapping
3. **Shibuya 3D Visualization** - Professional geospatial data processing and WebGL rendering

## Learning Path

### Phase 1: Python Fundamentals
Tutorial documents covering core concepts:
- [What is Programming](2026-01-30-what-is-programming.md) - Introduction to programming concepts
- [VS Code Basics](2026-01-30-vs-code-basics.md) - Development environment setup
- [Your First Python Program](2026-01-30-your-first-python-program.md) - Hello World and basic syntax
- [Variables](2026-01-30-variables.md) - Data storage and manipulation
- [User Input](2026-01-30-user-input.md) - Interactive programs
- [If Statements](2026-01-30-if-statements.md) & [Elif](2026-01-30-elif.md) - Conditional logic
- [Loops](2026-01-30-loops.md) - Iteration and repetition
- [Lists](2026-01-30-lists.md) - Data structures

### Phase 2: Hands-On Projects
Progressive exercises applying Python concepts:
- `001_hello.py` - First program
- `002_city_planner.py` through `009_isometric_city.py` - Building complexity through city simulation exercises
- Concepts: Data structures, loops, conditional logic, coordinate systems

### Phase 3: Real-World Geospatial Data
Multiple iterations solving increasing complexity:

**Version 1** (`build_shibuya_map_001.py`) - Learning XML parsing basics
**Version 2** (`build_shibuya_map_002.py`) - OSM data with isometric projection
**Version 3** (`build_shibuya_map_003.py`) - Introduction to PLATEAU data
**Version 4** (`build_shibuya_map_004.py`) - Production-ready LOD2 visualization

## Final Project: Shibuya 3D Map Visualization

A photorealistic 3D visualization of Shibuya Crossing demonstrating professional-level data engineering and visualization techniques.

### Features

- **High-detail building geometry**: PLATEAU LOD2 (Level of Detail 2) with detailed roof structures
- **Road network**: OpenStreetMap data via Overpass API
- **Interactive 3D view**: Three.js WebGL with orbit controls
- **Realistic rendering**: PBR materials with proper lighting and shadows
- **Spatial filtering**: 151 buildings within 200m radius of Shibuya Crossing
- **XLink resolution**: O(1) polygon lookup using pre-built cache

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

### Earlier Iterations (Learning Process)

- **`build_shibuya_map_001.py`** - Initial XML parsing exploration
- **`build_shibuya_map_002.py`** - OSM data with isometric rendering
- **`build_shibuya_map_003.py`** - First PLATEAU integration attempt
- **`build_shibuya_map_004.py`** - Final version with XLink resolution and road integration

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

## What I Learned

This project taught me that real-world data engineering is fundamentally about **understanding data formats**. The breakthrough moment was discovering that PLATEAU LOD2 uses XLink references - a detail not obvious from sample code or documentation. This required:

1. **Deep investigation** - Reading XML directly, testing ElementTree behavior, understanding why searches failed
2. **Performance thinking** - Recognizing that O(n²) lookups would be too slow, pre-building a cache
3. **Incremental debugging** - Adding detailed logging to understand what data actually looks like vs. what I expected

The progression from "hello world" to parsing government geospatial data demonstrates that complex projects are just **many simple steps combined thoughtfully**.

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

**From basic Python syntax to parsing government geospatial data in 4 iterations.** This repository documents the complete learning journey.
