#!/bin/bash

# Set a random wallpaper
WALLPAPER_DIR="$(dirname "$0")/../wallpapers"
WALLPAPER=$(find "$WALLPAPER_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) | shuf -n 1)

if [ -n "$WALLPAPER" ]; then
  # Example for feh or nitrogen; adjust for your setup
  if command -v feh &> /dev/null; then
    feh --bg-scale "$WALLPAPER"
  elif command -v nitrogen &> /dev/null; then
    nitrogen --set-zoom-fill "$WALLPAPER"
  else
    echo "[!] No supported wallpaper setter found."
  fi
else
  echo "[!] No wallpapers found in $WALLPAPER_DIR"
fi
