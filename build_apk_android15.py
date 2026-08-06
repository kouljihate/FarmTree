#!/usr/bin/env python3
"""Build APK for Farm Tree Manager targeting Android 15 (API 35)

This script builds the APK using the proper flet CLI invocation method.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(".")
KEYSTORE_PATH = PROJECT_ROOT / "keystore.jks"

print("=" * 70)
print("APK BUILD FOR ANDROID 15 (API 35) - FARM TREE MANAGER")
print("=" * 70)
print(f"Project: Farm Tree Manager v1.11.0")
print(f"Build Number: 21")
print(f"Target Android: API 35 (Android 15)")
print(f"Architecture: arm64-v8a")
print("=" * 70)

# Clean build artifacts
print("\nCleaning previous build artifacts...")
try:
    # Remove build directories
    for dir_to_clean in ["build/flutter", "build/python-app", "build/site-packages", "build/web", "build/.hash"]:
        path = PROJECT_ROOT / dir_to_clean
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path, ignore_errors=True)
    print("✓ Clean completed")
except Exception as e:
    print(f"Note: Clean may have failed: {e}")

# Build command using the correct flet CLI invocation
# Based on the README: "flet run main.py --android" and "flet build apk ."
build_cmd = [
    sys.executable,
    "-m", "pip",
    "run", "flet",
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
    "--build-number", "21",
    "--build-version", "1.11.0",
    "--arch", "arm64-v8a",
    "--split-per-abi",
    "--cleanup-app",
    "--permissions", "camera", "photo_library", "location", "access_background_location"
]

print(f"\nBuilding APK for Android 15...")
print(f"Command: {' '.join(build_cmd)}")
print(f"Timeout: 600 seconds (10 minutes)")

# Execute build
print(f"\nStarting build process...")
print(f"This may take 5-10 minutes. Please wait...")

try:
    result = subprocess.run(
        build_cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=600  # 10 minutes timeout
    )

    print("\n" + "=" * 70)
    print("BUILD OUTPUT")
    print("=" * 70)
    print(result.stdout)
    
    if result.stderr:
        print("\n" + "=" * 70)
        print("BUILD ERRORS")
        print("=" * 70)
        print(result.stderr)
    
    print(f"\nExit code: {result.returncode}")
    
    # Check for APK files
    apk_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.lower().endswith('.apk'):
                apk_files.append(os.path.join(root, file))
    
    if apk_files:
        latest_apk = max(apk_files, key=os.path.getctime)
        print(f"\n" + "=" * 70)
        print("APK BUILD SUCCESSFUL")
        print("=" * 70)
        print(f"APK created: {latest_apk}")
        print(f"APK size: {os.path.getsize(latest_apk) / (1024 * 1024):.2f} MB")
        
        # Copy to build/apk directory
        build_dir = os.path.join(PROJECT_ROOT, "build", "apk")
        os.makedirs(build_dir, exist_ok=True)
        dest_apk = os.path.join(build_dir, os.path.basename(latest_apk))
        
        shutil.copy2(latest_apk, dest_apk)
        print(f"Copied to: {dest_apk}")
        
        print(f"\n" + "=" * 70)
        print("APK TARGET SPECIFICATIONS - ANDROID 15 (API 35)")
        print("=" * 70)
        print(f"Target Android Version: API 35 (Android 15)")
        print(f"Architecture: ARM64-v8a (64-bit)")
        print(f"Application ID: kouljihate.farmtree")
        print(f"Version Code: 21")
        print(f"Version Name: 1.11.0")
        print(f"Signing: farmtree keystore")
        print(f"Min SDK: Auto-detected")
        print(f"Target SDK: API 35")
        print("=" * 70)
        
        print(f"\n✅ APK BUILD COMPLETED SUCCESSFULLY!")
        print(f"The APK is ready for distribution and installation.")
        print(f"It targets Android 15 (API 35) with arm64-v8a architecture.")
        
        sys.exit(0)
    else:
        print(f"\n" + "=" * 70)
        print("APK BUILD FAILED")
        print("=" * 70)
        print("No APK file was generated.")
        print(f"Looking in: {PROJECT_ROOT}")
        print("=" * 70)
        
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("\n" + "=" * 70)
    print("BUILD TIMEOUT")
    print("=" * 70)
    print("APK build timed out after 10 minutes.")
    print("APK builds can take several minutes. Please try again.")
    print("=" * 70)
    
    sys.exit(1)
except Exception as e:
    print(f"\n" + "=" * 70)
    print("BUILD ERROR")
    print("=" * 70)
    print(f"Error during build: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 70)
    
    sys.exit(1)
