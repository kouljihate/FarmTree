# FarmTree — Known Issues & Corrections

Reference for avoiding recurring bugs. Keep this file updated.

---

## 1. Dialog / Snackbar / BottomSheet API (flet 0.86.5)

**Symptom**: `page.snack_bar = ...`, `page.dialog = ...`, `page.overlay.append(bottomsheet)` silently do nothing — no error, no UI.

**Cause**: flet 0.86.5 removed property-setter API for dialogs and snackbars.

**Fix**:
```python
# Snackbar
page.show_snack(ft.SnackBar(ft.Text("msg")))

# Dialog
page.show_dialog(ft.AlertDialog(...))
page.pop_dialog()

# BottomSheet (is a DialogControl, NOT a page control)
page.show_dialog(bottomsheet)
page.pop_dialog()
```

**Never**: `page.snack_bar = x`, `page.dialog = x`, `page.overlay.append(bottomsheet)`

---

## 2. `FilledButton` / `OutlinedButton` have no `text=` kwarg

**Symptom**: `TypeError: unexpected keyword argument 'text'`

**Fix**:
```python
ft.FilledButton(icon=ft.Icons.SAVE, content=ft.Text("Save"), on_click=fn)
ft.OutlinedButton(content=ft.Text("Cancel"), on_click=fn)
```

---

## 3. `Audio` class lives in `flet_audio`, not `flet`

**Symptom**: `ImportError: cannot import name 'Audio' from 'flet'`

**Fix**:
```python
from flet_audio import Audio
```

---

## 4. `flet_audio_recorder` import crashes app on Android

**Symptom**: Red error bar "Unknown control: AudioRecorder" or app crash at startup.

**Cause**: flet's APK build system doesn't always bundle third-party control packages. Top-level `import flet_audio_recorder` crashes the entire app if the package is missing from the APK.

**Fix**:
```python
try:
    import flet_audio_recorder as far
except ImportError:
    far = None

# Later in setup_ui:
if far is not None:
    try:
        recorder = far.AudioRecorder(configuration=far.AudioRecorderConfiguration(...))
        page.overlay.append(recorder)
    except Exception as ex:
        logger.warning("Audio recorder init failed: %s", ex)
```

**Pattern**: ALL optional third-party controls (`flet_audio_recorder`, `flet_camera`, `flet_geolocator`) must be wrapped in `try/except ImportError` at import time AND at instantiation time.

---

## 4b. Python version mismatch causes "Unknown control"

**Symptom**: "Unknown control: AudioRecorder" persists even with try/except guard.

**Cause**: Two Python installations (3.12 and 3.14) with mismatched flet plugin versions. `flet build` uses system Python for packaging — if it picks the Python with outdated plugins (0.86.1 vs 0.86.5), native controls aren't registered.

**Fix**: Keep ALL flet packages at the SAME version across ALL Python installations:
```powershell
# Upgrade both Pythons to match
& "Python312\python.exe" -m pip install --upgrade flet flet-audio flet-audio-recorder flet-camera flet-charts flet-cli flet-geolocator
& "Python314\python.exe" -m pip install --upgrade flet flet-audio flet-audio-recorder flet-camera flet-charts flet-cli flet-geolocator
```

Also: **`RECORD_AUDIO` permission** must be in `--permissions` for AudioRecorder to work:
```python
"--permissions", "camera", "photo_library", "location", "microphone",
```

---

## 5. `AudioRecorder` must be registered in `main.py`, not in sub-views

**Symptom**: "Unknown control: AudioRecorder" when instantiated inside `add_view.py`.

**Cause**: flet controls must be registered at the page level before use. Sub-views don't have page access at import time.

**Fix**: Create and append `AudioRecorder` to `page.overlay` in `main.py` `setup_ui()`, then pass `self` (app reference) to views. Views access it via `self.app.audio_recorder`.

---

## 6. `page.clipboard` has no setter

**Symptom**: `AttributeError: property 'clipboard' of 'Page' object has no setter`

**Cause**: flet 0.86.5 `page.clipboard` is read-only.

**Fix**:
```python
page.set_clipboard(text)  # setter method
```

**Never**: `page.clipboard = text`

---

## 7. Firestore write / TinyDB read mismatch

**Symptom**: Trees saved but don't appear in list view.

**Cause**: `insert_tree` writes to Firestore but `get_trees_slice` / `count_trees` read from TinyDB directly, bypassing the active store.

**Fix**: `get_trees_slice` and `count_trees` must route through `get_all_trees()` which checks `firestore_db.is_available()` and reads from the active store.

```python
# database.py
def get_trees_slice(offset, limit):
    all_trees = get_all_trees()
    return all_trees[offset:offset+limit]

def count_trees():
    return len(get_all_trees())
```

---

## 8. Photo paths from Windows don't exist on Android

**Symptom**: Broken image icons in tree list cards on Android.

**Cause**: Photos saved with Windows paths (`C:\...`) don't exist on Android filesystem. List cards tried to load them as `Image` controls.

**Fix**: Remove photo loading from list cards. Show tree type icon instead. Photos only in detail view and visit cards (loaded from base64).

---

## 9. Base64 storage for photos and audio

**Symptom**: Firestore documents exceed 1MB limit with raw file data. File paths don't cross platforms.

**Fix**: Store photos and audio as base64 strings directly in Firestore documents.

```python
def photo_to_base64(path, max_px=800, quality=75):
    # Resize + compress JPEG, return base64 string

def audio_to_base64(path):
    # Read audio file, return base64 string
```

**Limits**: Photos ~50-100KB base64, audio ~30KB/s. Keep under 1MB total per document.

---

## 10. Build process — Python launcher dies mid-build

**Symptom**: Build appears to hang/fail, no APK produced.

**Cause**: Harness process cleanup kills the Python process. Gradle continues independently.

**Fix**:
1. Launch detached: `Start-Process -FilePath cmd -ArgumentList "/c run_build.bat" -WindowStyle Minimized`
2. Monitor Gradle output directory for APK: `build\flutter\build\app\outputs\apk\release\app-arm64-v8a-release.apk`
3. If Python dies but APK exists, copy manually:
   ```powershell
   Copy-Item "build\flutter\build\app\outputs\apk\release\app-arm64-v8a-release.apk" "build\apk\FarmTree-vX.Y.Z-arm64-v8a.apk"
   ```
4. Kill stale Java/Dart processes before rebuilding: `taskkill /f /im java.exe; taskkill /f /im dart.exe`

---

## 11. `flet build` APK artifact location

**Symptom**: Expected APK not at `build\apk\` — it's nested deeper.

**Actual path**: `build\flutter\build\app\outputs\apk\release\app-arm64-v8a-release.apk`

**Fix**: Always check the Gradle output directory and copy to `build\apk\` with the versioned name.

---

## 12. File locks during rebuild

**Symptom**: `rmdir /s /q build` hangs or fails.

**Cause**: Stale Java/Gradle processes hold file locks.

**Fix**: Always `taskkill /f /im java.exe` and `taskkill /f /im dart.exe` before deleting the build directory.

---

## 13. `Audio` playback from base64

**Symptom**: `Audio(src="data:audio/ogg;base64,...")` doesn't work on Android.

**Fix**: Decode base64 to temp file, play from file path:
```python
import base64, tempfile, os
data = base64.b64decode(audio_b64)
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
tmp.write(data)
tmp.close()
audio = ft.Audio(src=tmp.name, autoplay=True)
page.overlay.append(audio)
page.update()
# Clean up after playback
```

---

## 14. Version tracking

Always update these files together when bumping version:
- `version.py` — `"X.Y.Z"`
- `build_apk_android15.py` — `Build Number`, `--build-number`, `Version Code` (all same integer)
- `README.md` — `**Version**: X.Y.Z`

---

## 15. Clipboard API

```python
# flet 0.86.5
page.set_clipboard(text)   # SET
val = page.clipboard        # GET (read-only property)
```

---

## Quick Reference: flet 0.86.5 Control Registration

| Control | Where to register | Method |
|---|---|---|
| `Audio` | `page.overlay` | `page.overlay.append(audio)` |
| `Camera` | `page.overlay` | `page.overlay.append(camera)` |
| `AudioRecorder` | `page.overlay` | `page.overlay.append(recorder)` |
| `Geolocator` | `page.services` | `page.services.append(geolocator)` |
| `SnackBar` | `page.show_snack()` | Method, not property |
| `AlertDialog` | `page.show_dialog()` | Method, not property |
| `BottomSheet` | `page.show_dialog()` | It's a DialogControl |
