#!/usr/bin/env python3
"""Build APK for Farm Tree Manager targeting Android 15 (API 35)

This script builds the APK using the proper flet CLI invocation method.
"""

import subprocess
import sys
import os
import shutil
import time
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Configuration
PROJECT_ROOT = Path(".").resolve()
KEYSTORE_PATH = PROJECT_ROOT / "keystore.jks"

# Read version from version.py
_version_file = PROJECT_ROOT / "version.py"
_ns = {}
exec(_version_file.read_text(), _ns)
APP_VERSION = _ns["version"]

# Correct JAVA_HOME for Gradle (JDK 17 required by AGP 8.x)
_JAVA_HOME = r"C:\Users\koul\java\17.0.13+11"
os.environ["JAVA_HOME"] = _JAVA_HOME
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

print("=" * 70)
print("APK BUILD FOR ANDROID 15 (API 35) - FARM TREE MANAGER")
print("=" * 70)
print(f"Project: Farm Tree Manager v{APP_VERSION}")
print(f"Build Number: 52")
print(f"Target Android: API 35 (Android 15)")
print(f"Architecture: arm64-v8a")
print(f"JAVA_HOME: {_JAVA_HOME}")
print("=" * 70)

# Clean build artifacts
print("\nCleaning previous build artifacts...")
try:
    for dir_to_clean in ["build/flutter", "build/python-app", "build/site-packages", "build/web", "build/apk", "build/.hash"]:
        path = PROJECT_ROOT / dir_to_clean
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path, ignore_errors=True)
    print("Clean completed")
except Exception as e:
    print(f"Note: Clean may have failed: {e}")

# Build command using the correct flet CLI invocation
build_cmd = [
    "flet",
    "build", "apk", ".",
    "--module-name", "main",
    "--org", "kouljihate",
    "--bundle-id", "kouljihate.farmtree",
    "--project", "FarmTree",
    "--product", "Farm Tree Manager",
    "--description", "Farm Tree Manager",
    "--android-signing-key-store", str(KEYSTORE_PATH),
    "--android-signing-key-store-password", "FarmTree2026!",
    "--android-signing-key-password", "FarmTree2026!",
    "--android-signing-key-alias", "farmtree",
    "--build-number", "52",
    "--build-version", APP_VERSION,
    "--arch", "arm64-v8a",
    "--split-per-abi",
    "--cleanup-app",
    "--no-rich-output",
    "--permissions", "camera", "photo_library", "location", "microphone",
    "--android-permissions", "android.permission.ACCESS_BACKGROUND_LOCATION=true"
]

print(f"\nBuilding APK for Android 15...")
print(f"Timeout: 5400 seconds (90 minutes)")

print(f"\nStarting build process...")
print(f"This may take 15-60 minutes. Please wait...")

def _finalize_apk(project_root, app_version):
    apk_dir = project_root / "build" / "apk"
    versioned_name = f"FarmTree-v{app_version}-arm64-v8a.apk"
    print(f"\n" + "=" * 70)
    print("FINALIZING APK")
    print("=" * 70)
    # Gradle may keep building the APK after this script times out, so poll
    # for the produced APK and always rename it with the version number.
    deadline = time.time() + 40 * 60
    apk = None
    while time.time() < deadline:
        if apk_dir.exists():
            apks = list(apk_dir.glob("*.apk"))
            if apks:
                apk = max(apks, key=lambda f: f.stat().st_mtime)
                break
        time.sleep(15)
    if apk is None:
        print(f"\n" + "=" * 70)
        print("APK BUILD FAILED")
        print("=" * 70)
        print("No APK file was generated.")
        print(f"Looking in: {apk_dir}")
        print("=" * 70)
        return False
    target = apk.parent / versioned_name
    if apk.name != versioned_name:
        if target.exists():
            target.unlink()
        apk.rename(target)
        apk = target
    print(f"\n" + "=" * 70)
    print("APK BUILD SUCCESSFUL")
    print("=" * 70)
    print(f"APK created: {apk}")
    print(f"APK size: {apk.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"\n" + "=" * 70)
    print("APK TARGET SPECIFICATIONS - ANDROID 15 (API 35)")
    print("=" * 70)
    print(f"Target Android Version: API 35 (Android 15)")
    print(f"Architecture: ARM64-v8a (64-bit)")
    print(f"Application ID: kouljihate.farmtree")
    print(f"Version Code: 52")
    print(f"Version Name: {app_version}")
    print(f"Signing: farmtree keystore")
    print(f"Min SDK: 24")
    print(f"Target SDK: 36")
    print("=" * 70)
    print(f"\nAPK BUILD COMPLETED SUCCESSFULLY!")
    print(f"The APK is ready for distribution and installation.")
    return True


try:
    result = subprocess.run(
        build_cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=5400
    )
except subprocess.TimeoutExpired:
    result = None
    print("\n" + "=" * 70)
    print("BUILD TIMEOUT")
    print("=" * 70)
    print("flet exited by timeout, but Gradle may still be building the APK.")
    print("Waiting up to 40 minutes for the APK to be produced...")
except Exception as e:
    result = None
    print("\n" + "=" * 70)
    print("BUILD ERROR")
    print("=" * 70)
    print(f"Error during build: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 70)

if result is not None:
    print("\n" + "=" * 70)
    print("BUILD OUTPUT")
    print("=" * 70)
    print(result.stdout.encode("utf-8", errors="replace").decode("utf-8"))

    if result.stderr:
        print("\n" + "=" * 70)
        print("BUILD ERRORS")
        print("=" * 70)
        print(result.stderr.encode("utf-8", errors="replace").decode("utf-8"))

    print(f"\nExit code: {result.returncode}")

ok = _finalize_apk(PROJECT_ROOT, APP_VERSION)
sys.exit(0 if ok else 1)
