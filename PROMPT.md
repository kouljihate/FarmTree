# Farm Tree Manager - AI Prompt

You are working on **Farm Tree Manager** v1.11.0, a cross-platform Flet app for managing farm trees. Below are the conventions and patterns to follow.

## Project Overview

Mobile-first orchard management app: track trees by sector/zone/row/tree-number, record visits with photos, GPS locations, and statuses. Built with Flet (Python -> Flutter -> native).

## Architecture

```
main.py              # Entry point — single file, ~1750 lines
app/
  config.py          # TREE_KINDS, TREE_VARIETIES, TREE_STATUSES (color-coded)
  database.py        # TinyDB CRUD operations (insert, update, search, pagination, GPS)
  logger.py          # Rotating file logger
assets/fonts/        # Comfortaa-Regular.ttf font
data/                # trees.json (TinyDB) + photos/ (gitignored)
```

## Code Conventions

- **Single-file UI**: All UI lives in `main.py`. Break into app/ modules only for non-UI logic.
- **Imports**: Import individual controls from `flet` directly (e.g. `from flet import Page, Text, ...`). Keep the `Colors` and `Icons` enums imported.
- **State**: `TreesApp` class holds all state. Views (list, add, edit, detail, settings) are nested in a `Stack` and toggled via `visible`.
- **Database**: All queries go through `app.database` TinyDB functions. Never inline DB access in UI code.
- **Colors**: Use color constants from `Colors`. Status colors are the exception (defined in `config.py` `STATUS_LOOKUP`).
- **Routing**: View stack via `Container.visible` toggling — no router.
- **Responsive**: Fixed window size 420x780 (mobile-first).

## Key Dependencies

- `flet>=0.86.0` — UI framework
- `flet-camera>=0.86.0` — Camera integration (Android/iOS/Web only)
- `flet-charts>=0.86.0` — Charts (BarChart, PieChart, LineChart)
- `flet-geolocator>=0.86.0` — Device GPS location
- `flet-web>=0.86.0` — Web platform support
- `flet-cli>=0.86.0` — CLI build tools
- `flet-desktop>=0.86.0` — Desktop platform support
- `tinydb>=4.8.0` — lightweight document store (JSON file)

## Build Commands

| Command | Purpose |
|---------|---------|
| `python main.py` | Run desktop app |
| `flet run main.py --web` | Run as web app with hot reload |
| `python build_apk_android15.py` | Build signed release APK for Android 15 |

## Tree Kinds & Statuses

**Kinds** (from `app/config.py`): Cherry, Prunes, Nectarine, Peach, Citrus, Figue

**Statuses** (color-coded):
- Healthy `#2E7D32`, Needs Water `#1565C0`, Needs Fertilizer `#E65100`
- Diseased `#C62828`, Pest Infestation `#AD1457`, Pruned `#6A1B9A`
- Damaged `#BF360C`, Dead `#455A64`, Flowering `#C2185B`
- Fruiting `#F57F17`, New Planting `#558B2F`

When adding UI status indicators, use the color from `STATUS_LOOKUP[label]`.

## Platform Notes

- **Camera** (`flet-camera`): Only supported on Android, iOS, and Web. On desktop, camera features are gracefully disabled.
- **Geolocator** (`flet-geolocator`): Only supported on Android, iOS, and Web. On desktop, GPS features are gracefully disabled.
- **Charts** (`flet-charts`): BarChart used for statistics (trees per sector). Heatmap is manual grid.

## Testing

Tests are in the `Tests/` directory. Run with:
```bash
python -m pytest Tests/
```

## Style Guidelines

- **No comments in code** unless the logic is truly non-obvious.
- **Material Design 3** — use `Colors`, elevation, rounded corners.
- **Minimal output** — respond concisely, avoid preamble/postamble.
- **Prefer editing existing files** over creating new ones.
- **Match existing patterns** — look at how similar features are implemented before writing new code.
