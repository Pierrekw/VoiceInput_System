#!/usr/bin/env python3
"""Verify build files are correct"""

import os
import sys

def check_file(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✓ {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"✗ {description}: {filepath} NOT FOUND")
        return False

print("=" * 60)
print("Verifying Build Files")
print("=" * 60)

files_ok = True

# Check build scripts
files_ok &= check_file("build_nuitka.bat", "Windows build script")
files_ok &= check_file("build_nuitka_simple.sh", "Linux build script")

# Check configuration
files_ok &= check_file("nuitka.ini", "Nuitka config")
files_ok &= check_file("requirements-nuitka.txt", "Dependencies")

# Check documentation
files_ok &= check_file("BUILD_INSTRUCTIONS.md", "Build instructions")
files_ok &= check_file("NUITKA_PACKAGING_GUIDE.md", "Full guide")

# Check test
files_ok &= check_file("test_packaged_app.py", "Test script")

print("=" * 60)
if files_ok:
    print("✓ All build files are present")
    sys.exit(0)
else:
    print("✗ Some files are missing")
    sys.exit(1)
