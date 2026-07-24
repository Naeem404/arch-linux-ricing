#!/bin/bash
# Rofi screenshot menu: area, full screen, focused output, or focused window

DIR="$HOME/Pictures/Screenshots"
mkdir -p "$DIR"
FILE="$DIR/screenshot_$(date +%Y%m%d_%H%M%S).png"

MODE="${1:-menu}"

if [ "$MODE" = "menu" ]; then
    choice=$(printf 'Area\nFull Screen\nFocused Output\nFocused Window\n' | \
        rofi -dmenu \
            -no-custom \
            -a -1 \
            -click-to-exit \
            -theme-str 'mainbox { children: [listview]; } listview { lines: 4; }' \
            2>/dev/null | tr -d '\n')

    [ -z "$choice" ] && exit 0
    MODE="$choice"
fi

case "$MODE" in
    "Area"|"area")
        geom=$(slurp 2>/dev/null)
        [ -z "$geom" ] && exit 0
        grim -g "$geom" "$FILE"
        ;;
    "Full Screen"|"full")
        grim "$FILE"
        ;;
    "Focused Output"|"screen")
        output=$(niri msg focused-output 2>/dev/null | sed -n '1s/.*(\([^)]*\)).*/\1/p')
        [ -z "$output" ] && exit 1
        grim -o "$output" "$FILE"
        ;;
    "Focused Window"|"window")
        marker=$(mktemp)
        niri msg action screenshot-window >/dev/null 2>&1
        for _ in $(seq 1 30); do
            latest=$(find "$DIR" -maxdepth 1 -type f -name '*.png' -newer "$marker" -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
            if [ -n "$latest" ] && [ -s "$latest" ]; then
                FILE="$latest"
                break
            fi
            sleep 0.1
        done
        rm -f "$marker"
        ;;
    *)
        exit 0
        ;;
esac

if [ -f "$FILE" ] && [ -s "$FILE" ]; then
    if command -v wl-copy >/dev/null 2>&1; then
        wl-copy < "$FILE"
    fi
    notify-send -i camera-photo -t 3000 "Screenshot saved" "$FILE"
fi
