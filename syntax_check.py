#!/usr/bin/env python3

# Quick syntax check for main.py
import ast

with open('main.py', 'r') as f:
    try:
        ast.parse(f.read())
        print("✓ main.py syntax is valid")
    except SyntaxError as e:
        print(f"✗ Syntax error in main.py: {e}")
        print(f"  Line {e.lineno}: {e.text}")
"