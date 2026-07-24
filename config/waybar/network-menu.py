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


def kill_existing(script):
    current = os.getpid()
    try:
        out = subprocess.check_output(['pgrep', '-af', script], text=True)
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
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def kill_others():
    kill_existing('network-menu.py')
    kill_existing('bluetooth-menu.py')
    kill_existing('volume-menu.py')
    subprocess.run(['pkill', '-x', 'rofi'], capture_output=True)


def active_wifi():
    try:
        out = subprocess.check_output(
            ['nmcli', '-t', '-f', 'name,device,type', 'connection', 'show', '--active'],
            text=True, stderr=subprocess.DEVNULL).strip()
        for line in out.splitlines():
            parts = line.split(':')
            if len(parts) >= 3 and parts[2] == '802-11-wireless':
                return parts[0]
    except Exception:
        pass
    return None


def wifi_networks():
    networks = []
    try:
        out = subprocess.check_output(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,IN-USE', 'device', 'wifi', 'list'],
            text=True, stderr=subprocess.DEVNULL).strip()
        for line in out.splitlines():
            parts = line.split(':', 3)
            if len(parts) >= 4 and parts[0] and parts[1]:
                ssid = parts[0]
                signal = parts[1]
                security = parts[2]
                in_use = parts[3] == '*'
                networks.append((ssid, signal, security, in_use))
    except Exception:
        pass
    return networks


def saved_wifi_profiles():
    profiles = set()
    try:
        out = subprocess.check_output(
            ['nmcli', '-t', '-f', 'name,type', 'connection', 'show'],
            text=True, stderr=subprocess.DEVNULL).strip()
        for line in out.splitlines():
            parts = line.split(':', 1)
            if len(parts) >= 2 and parts[1] == '802-11-wireless':
                profiles.add(parts[0])
    except Exception:
        pass
    return profiles


class NetworkMenu(Gtk.Window):
    def __init__(self):
        super().__init__(title='Network')
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_size_request(300, -1)

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
        label {
            font-size: 13px;
        }
        label.header {
            font-weight: bold;
            font-size: 14px;
        }
        label.active {
            color: #ffffff;
            font-weight: bold;
        }
        button {
            background-color: transparent;
            border: 1px solid #3a3a3a;
            border-radius: 8px;
            padding: 6px 12px;
        }
        button:hover {
            background-color: #3a3a3a;
        }
        list {
            background-color: transparent;
        }
        list row {
            background-color: transparent;
            border: none;
            padding: 4px 0;
        }
        list row:selected {
            background-color: #3a3a3a;
        }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'waybar-network')
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

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(14)
        box.set_margin_bottom(14)
        box.set_margin_start(14)
        box.set_margin_end(14)
        self.add(box)

        header = Gtk.Label(label='Network')
        header.get_style_context().add_class('header')
        header.set_xalign(0)
        box.pack_start(header, False, False, 0)

        active = active_wifi()
        if active:
            status = Gtk.Label(label=f'Connected: {active}')
            status.get_style_context().add_class('active')
        else:
            status = Gtk.Label(label='Not connected')
        status.set_xalign(0)
        box.pack_start(status, False, False, 0)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        box.pack_start(listbox, True, True, 0)

        networks = wifi_networks()
        if not networks:
            row = Gtk.ListBoxRow()
            lab = Gtk.Label(label='No networks found')
            lab.set_xalign(0)
            row.add(lab)
            listbox.add(row)
        else:
            for ssid, signal, security, in_use in networks:
                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                label = Gtk.Label(label=f'{ssid}  ({signal}%)')
                label.set_xalign(0)
                hbox.pack_start(label, True, True, 0)
                btn = Gtk.Button(label='Connect')
                if in_use:
                    btn.set_label('Connected')
                    btn.set_sensitive(False)
                btn.connect('clicked', self.on_connect, ssid)
                hbox.pack_end(btn, False, False, 0)
                row.add(hbox)
                listbox.add(row)

        mbtn = Gtk.Button(label='Open Network Manager')
        mbtn.connect('clicked', self.open_manager)
        box.pack_start(mbtn, False, False, 0)

        self.connect('key-press-event', self.on_key)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('destroy', Gtk.main_quit)
        self.show_all()
        self.set_focus(mbtn)

    def on_connect(self, button, ssid):
        profiles = saved_wifi_profiles()
        if ssid in profiles:
            subprocess.Popen(
                ['nmcli', 'connection', 'up', ssid],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(
                ['nmcli', 'device', 'wifi', 'connect', ssid, 'ifname', 'wlan0'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Gtk.main_quit()

    def open_manager(self, button):
        subprocess.Popen(['nmgui'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Gtk.main_quit()

    def on_key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()
        return False

    def on_focus_out(self, widget, event):
        Gtk.main_quit()
        return False


if __name__ == '__main__':
    kill_others()
    NetworkMenu()
    Gtk.main()
