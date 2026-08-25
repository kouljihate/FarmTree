# Farm Tree Manager

A cross-platform mobile application for managing farm trees, built with Flet (Flutter for Python).

## Project Status

This is a **complete working application** with the following structure:

### Core Files

#### `main.py` (~457 lines)
- App entry point, navigation, and view orchestration
- GPS and camera service initialization (overlay-based for Camera)
- Context menus, status picker, history bottom sheet
- Desktop-only window sizing (Android/mobile unaffected)

#### `app/views/` - UI Views
- `add_view.py` (~450 lines) - Add tree form with GPS, photo, and details
- `edit_view.py` (~227 lines) - Edit tree and add visits with camera support
- `detail_view.py` (~158 lines) - Tree detail display
- `list_view.py` (~215 lines) - Tree list with pagination and search
- `settings_view.py` (~163 lines) - Language switch, help, about, logs
- `stats_view.py` (~246 lines) - Statistics: heatmap + bar chart
- `components.py` (~255 lines) - Shared UI, TRANSLATIONS (en/ar), build_visit_card()

#### `app/config.py` (109 lines)
- `TREE_KINDS`: Cherry, Prunes, Nectarine, Peach, Citrus, Figue
- `TREE_VARIETIES`: Detailed variety mappings for each kind
- `TREE_STATUSES`: Color-coded status list with hex colors
- `STATUS_LOOKUP`: Dictionary mapping status labels to colors

#### `app/database.py` (257 lines)
- TinyDB CRUD operations using document-based storage
- Functions for inserting, updating, searching, and paginating trees
- Caching layer for performance

#### `app/logger.py` (50 lines)
- Rotating file logger with 5MB max size and 3 backup files
- Logs at DEBUG level to `data/logs/app.log`

### Supporting Files

- `assets/fonts/Comfortaa-Regular.ttf` - Typography font
- `assets/fonts/AlMaghrebi-Modern-Wahib.ttf` - Arabic font
- `data/trees.json` - TinyDB document store
- `data/photos/` - Photo storage directory (gitignored)
- `version.py` - Version string

### Tests/

- `generate_trees.py` - Generates 25,000 sample trees
- `clean_db.py` - Clears all data from database and photos

### Build Tools

- `build_apk_android15.py` - Android APK build script (JDK 17, UTF-8)
- `requirements.txt` - Dependencies

### Key Features

- Tree management (add, edit, delete)
- GPS location capture (flet-geolocator)
- Photo capture from camera (flet-camera, overlay-based)
- Visit tracking with status/notes
- Real-time search and filtering
- Efficient pagination
- Status picker with color badges
- Statistics: heatmap + bar chart (flet-charts)
- Material Design 3 components
- Cross-platform support (Android, iOS, Web, Desktop)
- Performance optimized with caching
- Comprehensive logging
- Arabic/English language support

### Architecture

- **Mobile-first**: Responsive layout (window sizing only on desktop)
- **Modular views**: Each view in `app/views/` with setup/show pattern
- **Camera as overlay**: Camera widget mounted in `page.overlay` (not services)
- **View stacking**: Uses `Container.visible` for routing
- **BottomSheet cleanup**: Old sheets removed before each new one
- **TinyDB**: Lightweight JSON document store
- **Responsive design** with Material Design 3

### Technologies

- **Flet** - Flutter UI for Python
- **flet-camera** - Camera integration
- **flet-charts** - Charts (BarChart, PieChart, LineChart)
- **flet-geolocator** - Device GPS location
- **TinyDB** - Document-based JSON storage
- **Python 3.12+**
- **Cross-platform** support (Android, iOS, Web, Desktop)

### Build Commands

```bash
# Desktop
python main.py

# Web with hot reload
flet run main.py --web

# Android APK (requires JDK 17)
python build_apk_android15.py
```

### Build Requirements

- **JDK 17** (required by Gradle 8.14 / AGP 8.11.1)
- **Android SDK** with platforms up to API 35+
- **Flutter** 3.44+
- **PYTHONUTF8=1** for Windows console emoji support

---

**Status**: COMPLETE WORKING APPLICATION
**Version**: 1.13.0
