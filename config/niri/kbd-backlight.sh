#!/bin/bash
# Cycle ASUS keyboard backlight (0 -> 1 -> 2 -> 3 -> 0)

DEV='asus::kbd_backlight'

cur=$(brightnessctl -d "$DEV" get 2>/dev/null)
max=$(brightnessctl -d "$DEV" max 2>/dev/null)

[ -z "$cur" ] || [ -z "$max" ] && exit 0

next=$((cur + 1))
[ "$next" -gt "$max" ] && next=0

brightnessctl -d "$DEV" set "$next" >/dev/null 2>&1
