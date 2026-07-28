# Farm Tree Manager

A cross-platform mobile application for managing farm trees, built with [Flet](https://flet.dev/) (Flutter for Python).

## Features

- **Tree Management**: Add, edit, and delete trees with sector, zone, row, and tree number
- **GPS Location**: Auto-fill latitude/longitude using device GPS
- **Photo Capture**: Take photos using camera or select from gallery
- **Visit Tracking**: Record visits with status, notes, and photos
- **Search & Filter**: Real-time search and filter by kind, status
- **Pagination**: Efficient loading of large tree lists
- **Voice Recording**: Voice input for notes (where supported)
- **Cross-platform**: Works on Android, iOS, Web, and Desktop

## Screenshots

| Tree List | Add Tree | Tree Detail |
|-----------|----------|-------------|
| *Tree listing with pagination* | *Form with GPS and camera* | *Detail view with visits* |

## Tech Stack

- **Framework**: [Flet](https://flet.dev/) - Flutter UI for Python
- **Database**: TinyDB (JSON document store)
- **Language**: Python 3.10+
- **Platform**: Android, iOS, Web, Windows, macOS, Linux

## Installation

### Prerequisites
- Python 3.10+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/farm-tree-manager.git
cd farm-tree-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
# Desktop
python main.py

# Android (requires Flet CLI)
flet run main.py --android

# Web
flet run main.py --web
```

## Project Structure

```
farm-tree-manager/
├── main.py              # Main application entry point
├── version.py           # Version information
├── requirements.txt     # Python dependencies
├── PROMPT.md            # AI prompt / conventions
├── .gitignore           # Git ignore rules
├── app/
│   ├── config.py        # Tree kinds, statuses configuration
│   ├── database.py      # TinyDB CRUD operations
│   └── logger.py        # Rotating file logger
├── assets/
│   └── fonts/
│       └── Comfortaa-Regular.ttf
├── data/
│   ├── trees.json       # TinyDB document store
│   └── photos/          # Captured photos storage
├── build/
│   ├── build_apk.bat    # APK build script
│   └── apk/             # Built APK output
└── Tests/               # Test scripts
```

## Database

Uses **TinyDB** (JSON document store) at `data/trees.json`. Each tree document contains:
- `tree_code`, `kind`, `variety`, `latitude`, `longitude`
- `visits[]` — array of visit objects with `visit_dt`, `status`, `notes`, `photos[]`

## Key Features Implementation

### Camera Integration
- Camera button launches device camera directly
- Gallery button opens photo library
- Photos are copied to app storage and referenced by path

### GPS Location
- Uses Flet's `Geolocator` for device location
- Auto-fills latitude/longitude fields
- Shows location permissions dialog

### Search & Filter
- Real-time search as you type
- Filter by tree kind and status
- Pagination for large datasets

### UI Components
- Material Design 3 components
- Custom `Card` layouts for Location, Tree Details, Photos
- Responsive design for mobile and desktop
- Comfortaa font for consistent typography

## Configuration

### Tree Kinds (app/config.py)
```python
TREE_KINDS = [
    "Oak", "Pine", "Maple", "Birch", "Cedar",
    "Spruce", "Fir", "Willow", "Elm", "Ash",
    # ... more kinds
    "Other"
]
```

### Tree Statuses (app/config.py)
```python
TREE_STATUSES = [
    (1, "Healthy", "#2E7D32"),
    (2, "Needs Water", "#1565C0"),
    (3, "Needs Fertilizer", "#E65100"),
    # ... more statuses
]
```

## Building for Production

### Android APK
```bash
flet build apk main.py
```

### iOS
```bash
flet build ios main.py
```

### Web
```bash
flet build web main.py
```

## Dependencies

See `requirements.txt`:
- flet>=0.85.0
- python-dotenv (for environment variables)

## License

MIT License - feel free to use and modify for your farm management needs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Version History

- **v1.8.0** - TopBar redesign, status badge styling improvements, AppBar navigation enhancements
- **v1.7.0** - Code optimisations, refactored save methods, Android 15 (API 35) target, updated build tooling
- **v1.6.0** - Build 15, TinyDB migration, Pomme -> Prunes rename
- **v1.5.0** - Enhanced tree varieties, Bug fixes
- **v1.2.0** - Camera integration, GPS, Card-based UI layout
- **v1.0.0** - initial release

---

Built with ❤️ using [Flet](https://flet.dev/)