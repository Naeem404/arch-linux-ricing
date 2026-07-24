#!/bin/bash
set -e

# Install packages from lists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$SCRIPT_DIR/../pkg"

echo "[*] Installing official packages..."
xargs -a "$PKG_DIR/pacman.txt" sudo pacman -S --needed --noconfirm

if command -v yay &> /dev/null; then
  echo "[*] Installing AUR packages..."
  xargs -a "$PKG_DIR/aur.txt" yay -S --needed --noconfirm
else
  echo "[!] yay not found. Skipping AUR packages."
fi
