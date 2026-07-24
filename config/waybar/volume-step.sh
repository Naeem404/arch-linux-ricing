#!/bin/bash
# Volume step with GTK+layer-shell OSD

DEFAULT='@DEFAULT_AUDIO_SINK@'

case "$1" in
    up)
        wpctl set-mute "$DEFAULT" 0
        wpctl set-volume "$DEFAULT" 0.05+ -l 1.0
        ;;
    down)
        wpctl set-mute "$DEFAULT" 0
        wpctl set-volume "$DEFAULT" 0.05-
        ;;
    mute)
        wpctl set-mute "$DEFAULT" toggle
        ;;
    *)
        exit 0
        ;;
esac

"$HOME/.config/waybar/volume-osd.py" >/dev/null 2>&1 &
