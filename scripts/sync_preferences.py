#!/usr/bin/env python3
"""
sync_preferences.py — Helper to refresh preferences.json after editing preferences.md.

This is a placeholder. The intake task (intake.md) writes preferences.json
directly using the AI. If you edit preferences.md by hand, you have two options:

  1. Edit preferences.json directly (preferred — it's a flat JSON file).
  2. Ask the AI to re-sync: "Read preferences.md and update preferences.json
     to match."

The format is intentionally simple so the AI can rebuild it from preferences.md
without needing a brittle markdown parser.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PREFS_MD = BASE_DIR / "preferences.md"
PREFS_JSON = BASE_DIR / "preferences.json"


def main():
    if not PREFS_MD.exists():
        sys.exit(f"ERROR: {PREFS_MD} not found.")
    if not PREFS_JSON.exists():
        sys.exit(f"ERROR: {PREFS_JSON} not found.")

    print("preferences.md and preferences.json both exist.")
    print()
    print("To sync changes from preferences.md → preferences.json, either:")
    print("  1. Edit preferences.json directly (it's a simple JSON file).")
    print('  2. Ask the AI: "Read preferences.md and update preferences.json to match."')
    print()
    print("To sync changes from preferences.md → preferences.json, either:")
    print("This script is intentionally a no-op; the AI handles the parsing.")


if __name__ == "__main__":
    main()
