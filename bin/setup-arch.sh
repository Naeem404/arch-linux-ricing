#!/bin/bash
set -e

# Arch Linux ricing setup script

echo "[*] Setting up Arch Linux ricing environment..."

# Update system
sudo pacman -Syu --noconfirm

# Install packages
xargs -a "$(dirname "$0")/../pkg/pacman.txt" sudo pacman -S --needed --noconfirm

# Install AUR packages (requires an AUR helper like yay)
if command -v yay &> /dev/null; then
  xargs -a "$(dirname "$0")/../pkg/aur.txt" yay -S --needed --noconfirm
fi

# Apply dotfiles
"$(dirname "$0")/apply-dotfiles.sh"

echo "[+] Setup complete. Reboot or log out to apply all changes."
