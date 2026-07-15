#!/usr/bin/env python3

# Quick script to search for bottom appbar references in main.py
with open('main.py', 'r') as f:
    content = f.read()

# Find all lines that might contain bottom bar references
lines = content.split('\n')

print('=== Searching for BottomBar or Bottom AppBar references ===')
for i, line in enumerate(lines, 1):
    if any(keyword in line.lower() for keyword in ['bottom', 'bar', 'appbar']):
        print(f'Line {i}: {line}')