#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell

DEFAULT = '@DEFAULT_AUDIO_SINK@'
CLOSE_MS = 1500

def kill_existing():
    current = os.getpid()
    try:
        out = subprocess.check_output(['pgrep', '-af', 'volume-osd.py'], text=True)
    except subprocess.CalledProcessError:
        return
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

def current_state():
    try:
        out = subprocess.check_output(['wpctl', 'get-volume', DEFAULT],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        raw = out.split()
        val = float(raw[-1])
        muted = any('MUTED' == p.upper() for p in raw)
        return int(round(val * 100)), muted
    except Exception:
        return 50, False

class VolumeOSD(Gtk.Window):
    def __init__(self):
        super().__init__(title='Volume OSD')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_size_request(220, 56)

        css = b'''
        * {
            color: #d7d7d7;
            background-color: transparent;
            outline: none;
        }
        window {
            background-color: #0d0d0d;
            border: 1px solid #3a3a3a;
            border-radius: 12px;
        }
        progressbar trough {
            background-color: #3a3a3a;
            border-radius: 6px;
            min-height: 12px;
        }
        progressbar progress {
            background-color: #d7d7d7;
            border-radius: 6px;
            min-height: 12px;
        }
        progressbar text {
            color: #d7d7d7;
            font: monospace 11;
        }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'waybar-volume-osd')
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, 1)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, 1)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, 1)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 36)
        GtkLayerShell.set_exclusive_zone(self, -1)
        if hasattr(GtkLayerShell.KeyboardMode, 'ON_DEMAND'):
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)
        else:
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        self.add(box)

        vol, muted = current_state()
        self.bar = Gtk.ProgressBar()
        self.bar.set_show_text(True)
        self.bar.set_hexpand(True)
        if muted:
            self.bar.set_fraction(0.0)
            self.bar.set_text('muted')
        else:
            self.bar.set_fraction(vol / 100.0)
            self.bar.set_text(f'{vol}%')
        box.add(self.bar)

        self.connect('key-press-event', self.on_key_press)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('destroy', Gtk.main_quit)

        self.show_all()
        GLib.timeout_add(CLOSE_MS, Gtk.main_quit)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
        return False

    def on_focus_out(self, widget, event):
        Gtk.main_quit()
        return False

if __name__ == '__main__':
    kill_existing()
    VolumeOSD()
    Gtk.main()
