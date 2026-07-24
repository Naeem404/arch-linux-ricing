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
    kill_existing('bluetooth-menu.py')
    kill_existing('network-menu.py')
    kill_existing('volume-menu.py')
    subprocess.run(['pkill', '-x', 'rofi'], capture_output=True)


def bt_power():
    try:
        out = subprocess.check_output(['bluetoothctl', 'show'],
                                      text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if 'Powered:' in line:
                return line.split()[-1] == 'yes'
    except Exception:
        pass
    return False


def bt_devices():
    devices = []
    try:
        out = subprocess.check_output(['bluetoothctl', 'devices'],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        for line in out.splitlines():
            if line.startswith('Device '):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    devices.append((parts[1], parts[2]))
    except Exception:
        pass
    return devices


def bt_connected(mac):
    try:
        out = subprocess.check_output(['bluetoothctl', 'info', mac],
                                      text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if 'Connected:' in line:
                return line.split()[-1] == 'yes'
    except Exception:
        pass
    return False


class BluetoothMenu(Gtk.Window):
    def __init__(self):
        super().__init__(title='Bluetooth')
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
            font-size: 15px;
        }
        label.connected {
            font-weight: bold;
            color: #ffffff;
        }
        label.dim {
            color: #888888;
        }
        button {
            background-color: transparent;
            border: 1px solid #3a3a3a;
            border-radius: 8px;
            padding: 5px 12px;
            min-width: 90px;
        }
        button:hover {
            background-color: #3a3a3a;
        }
        separator {
            background-color: #3a3a3a;
            min-height: 1px;
            margin: 6px 0;
        }
        list {
            background-color: transparent;
        }
        list row {
            background-color: transparent;
            border: none;
            padding: 5px 0;
        }
        '''
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'waybar-bluetooth')
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

        header = Gtk.Label(label='Bluetooth')
        header.get_style_context().add_class('header')
        header.set_xalign(0)
        box.pack_start(header, False, False, 0)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        box.pack_start(listbox, True, True, 0)

        devices = bt_devices()
        if not devices:
            row = Gtk.ListBoxRow()
            lab = Gtk.Label(label='No paired devices')
            lab.get_style_context().add_class('dim')
            lab.set_xalign(0)
            row.add(lab)
            listbox.add(row)
        else:
            for mac, name in devices:
                connected = bt_connected(mac)
                row = Gtk.ListBoxRow()
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                label = Gtk.Label(label=name)
                label.set_xalign(0)
                if connected:
                    label.get_style_context().add_class('connected')
                hbox.pack_start(label, True, True, 0)
                btn = Gtk.Button(label='Disconnect' if connected else 'Connect')
                btn.set_size_request(90, -1)
                btn.connect('clicked', self.on_toggle, mac, connected)
                hbox.pack_end(btn, False, False, 0)
                row.add(hbox)
                listbox.add(row)

        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        power = bt_power()
        pbtn = Gtk.Button(label=f'Turn Bluetooth {"Off" if power else "On"}')
        pbtn.connect('clicked', self.on_power, power)
        box.pack_start(pbtn, False, False, 0)

        mbtn = Gtk.Button(label='Open Bluetooth Manager')
        mbtn.connect('clicked', self.open_manager)
        box.pack_start(mbtn, False, False, 0)

        self.connect('key-press-event', self.on_key)
        self.connect('focus-out-event', self.on_focus_out)
        self.connect('destroy', Gtk.main_quit)
        self.show_all()
        self.set_focus(mbtn)

    def on_toggle(self, button, mac, was_connected):
        if was_connected:
            subprocess.Popen(['bluetoothctl', 'disconnect', mac],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(['bluetoothctl', 'connect', mac],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Gtk.main_quit()

    def on_power(self, button, was_on):
        subprocess.Popen(['bluetoothctl', 'power', 'off' if was_on else 'on'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Gtk.main_quit()

    def open_manager(self, button):
        subprocess.Popen(['blueman-manager'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    BluetoothMenu()
    Gtk.main()
