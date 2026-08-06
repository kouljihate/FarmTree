# Farm Tree Manager

A cross-platform mobile application for managing farm trees, built with Flet (Flutter for Python).

## Project Status

This is a **complete working application** with the following structure:

### Core Files

#### `main.py` (~1,750 lines)
- Single-file UI containing all views (list, add, edit, detail, settings, stats)
- Implements tree management features including:
  - Add/edit/delete trees with sector/zone/row/tree-number format
  - GPS location capture via flet-geolocator
  - Photo capture from camera via flet-camera
  - Visit tracking with status and notes
  - Real-time search and filtering
  - Pagination for large datasets
  - Status picker with color-coded badges
  - Statistics with heatmap and bar chart (flet-charts)

#### `app/config.py`
- `TREE_KINDS`: Cherry, Prunes, Nectarine, Peach, Citrus, Figue
- `TREE_VARIETIES`: Detailed variety mappings for each kind
- `TREE_STATUSES`: Color-coded status list with hex colors
- `STATUS_LOOKUP`: Dictionary mapping status labels to colors

#### `app/database.py`
- TinyDB CRUD operations using document-based storage
- Functions for inserting, updating, searching, and paginating trees
- GPS location support via flet-geolocator
- Caching layer for performance

#### `app/logger.py`
- Rotating file logger with 5MB max size and 3 backup files
- Logs at DEBUG level to `data/logs/app.log`

### Supporting Files

- `assets/fonts/Comfortaa-Regular.ttf` - Typography font
- `data/trees.json` - TinyDB document store
- `data/photos/` - Photo storage directory (gitignored)
- `version.py` - Version 1.11.0

### Tests/

- `generate_trees.py` - Generates 25,000 sample trees
- `clean_db.py` - Clears all data from database and photos

### Build Tools

- `build_apk_android15.py` - Android APK build script for Android 15 (API 35)
- `requirements.txt` - Dependencies

### Key Features

- Tree management (add, edit, delete)
- GPS location capture (flet-geolocator)
- Photo capture from camera (flet-camera)
- Visit tracking with status/notes
- Real-time search and filtering
- Efficient pagination
- Status picker with color badges
- Statistics: heatmap + bar chart (flet-charts)
- Material Design 3 components
- Cross-platform support (Android, iOS, Web, Desktop)
- Performance optimized with caching
- Comprehensive logging

### Architecture

- **Mobile-first**: Fixed window size 420x780
- **Single-file UI**: All UI in `main.py`
- **Modular structure**: Non-UI logic in `app/` modules
- **View stacking**: Uses `Container.visible` for routing
- **TinyDB**: Lightweight JSON document store
- **Responsive design** with Material Design 3

### Technologies

- **Flet** - Flutter UI for Python
- **flet-camera** - Camera integration
- **flet-charts** - Charts (BarChart, PieChart, LineChart)
- **flet-geolocator** - Device GPS location
- **flet-web** - Web platform support
- **flet-cli** - CLI build tools
- **flet-desktop** - Desktop platform support
- **TinyDB** - Document-based JSON storage
- **Python 3.12+**
- **Cross-platform** support

### Build Commands

```bash
# Desktop
python main.py

# Web with hot reload
flet run main.py --web

# Android APK
python build_apk_android15.py
```

---

**Status**: COMPLETE WORKING APPLICATION
