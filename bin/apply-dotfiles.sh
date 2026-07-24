#!/bin/bash
set -e

# Symlink dotfiles into place
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR/.."

echo "[*] Applying dotfiles..."

# .config directories
for dir in "$REPO_DIR"/config/*/; do
  name=$(basename "$dir")
  target="$HOME/.config/$name"
  if [ -d "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.backup.$(date +%s)"
  fi
  ln -sfn "$dir" "$target"
  echo "[+] Linked ~/.config/$name"
done

# Home dotfiles
for file in "$REPO_DIR"/home/.*; do
  [ -e "$file" ] || continue
  name=$(basename "$file")
  target="$HOME/$name"
  if [ -f "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.backup.$(date +%s)"
  fi
  ln -sfn "$file" "$target"
  echo "[+] Linked ~/$name"
done

echo "[+] Dotfiles applied."
