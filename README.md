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
- **Database**: SQLite with custom schema
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
├── .gitignore           # Git ignore rules
├── app/
│   ├── __init__.py
│   ├── config.py        # Tree kinds, statuses configuration
│   └── database.py      # SQLite database operations
├── assets/
│   └── fonts/
│       └── Comfortaa-Regular.woff2
├── data/
│   ├── farm_trees.db    # SQLite database (created on first run)
│   └── photos/          # Captured photos storage
└── build/               # Build output directory
```

## Database Schema

```sql
-- Trees table
CREATE TABLE trees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tree_code TEXT UNIQUE NOT NULL,
    sector TEXT NOT NULL,
    zone TEXT NOT NULL,
    row_num TEXT NOT NULL,
    tree_number TEXT NOT NULL,
    kind TEXT NOT NULL,
    variety TEXT,
    latitude REAL,
    longitude REAL,
    status TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Visits table
CREATE TABLE visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tree_id INTEGER NOT NULL,
    visit_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    notes TEXT,
    photos TEXT,  -- JSON array of photo paths
    FOREIGN KEY (tree_id) REFERENCES trees (id) ON DELETE CASCADE
);
```

## Key Features Implementation

### Camera Integration
- Uses Flet's `FilePicker` with `FilePickerFileType.IMAGE`
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

- **v1.2.0** - Added camera integration, GPS, Card-based UI layout
- **v1.1.0** - Added search, pagination, visit tracking
- **v1.0.0** - Initial release with basic CRUD operations

---

Built with ❤️ using [Flet](https://flet.dev/)