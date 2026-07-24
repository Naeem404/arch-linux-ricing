#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GtkLayerShell

DEFAULT = '@DEFAULT_AUDIO_SINK@'

def kill_existing():
    current = os.getpid()
    killed = False
    try:
        out = subprocess.check_output(['pgrep', '-af', 'volume-menu.py'], text=True)
    except subprocess.CalledProcessError:
        return killed
    for line in out.strip().split('\n'):
        parts = line.split()
        if not parts:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        if pid != current:
            os.kill(pid, signal.SIGTERM)
            killed = True
    return killed

def kill_rofi():
    subprocess.run(['pkill', '-x', 'rofi'], capture_output=True)

def current_volume():
    try:
        out = subprocess.check_output(['wpctl', 'get-volume', DEFAULT],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        return int(round(float(out.split()[-1]) * 100))
    except Exception:
        return 50

def set_volume(value):
    value = int(round(value))
    subprocess.run(['wpctl', 'set-mute', DEFAULT, '0'],
                   capture_output=True)
    subprocess.run(['wpctl', 'set-volume', DEFAULT, f'{value}%'],
                   capture_output=True)

class VolumeSlider(Gtk.Window):
    def __init__(self):
        super().__init__(title='Volume')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_size_request(64, 260)

        # Monochrome dark styling
        css = b'''
        * {
            font-family: "FreeSans", sans-serif;
            color: #d7d7d7;
            background-color: transparent;
            outline: none;
        }
        window {
            background-color: #0d0d0d;
            border: 1px solid #3a3a3a;
            border-radius: 12px;
        }
        scale.vertical slider {
            background-color: #d7d7d7;
            border-radius: 50%;
            min-width: 14px;
            min-height: 14px;
            margin: -6px;
        }
        scale.vertical trough {
            background-color: #3a3a3a;
            border-radius: 6px;
            min-width: 8px;
            min-height: 160px;
        }
        scale.vertical highlight {
            background-color: #d7d7d7;
            border-radius: 6px;
        }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Layer-shell: top-right, just under the bar
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'waybar-volume')
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 36)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 10)
        GtkLayerShell.set_exclusive_zone(self, -1)
        if hasattr(GtkLayerShell.KeyboardMode, 'ON_DEMAND'):
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        else:
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(14)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        self.add(box)

        # Vertical volume scale
        adj = Gtk.Adjustment(value=current_volume(), lower=0,
                             upper=100, step_increment=5,
                             page_increment=5, page_size=0)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL, adjustment=adj)
        self.scale.set_inverted(True)
        self.scale.set_draw_value(True)
        self.scale.set_value_pos(Gtk.PositionType.TOP)
        self.scale.set_vexpand(True)
        self.scale.set_size_request(40, 180)
        box.add(self.scale)

        self.scale.connect('value-changed', self.on_value_changed)
        self.connect('key-press-event', self.on_key_press)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('destroy', Gtk.main_quit)

        self.show_all()

    def on_value_changed(self, scale):
        set_volume(scale.get_value())

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
        return False

    def on_focus_out(self, widget, event):
        Gtk.main_quit()
        return False

if __name__ == '__main__':
    if kill_existing():
        sys.exit(0)
    kill_rofi()
    VolumeSlider()
    Gtk.main()
