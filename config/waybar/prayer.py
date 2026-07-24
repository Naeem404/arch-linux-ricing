#!/usr/bin/env python3
import json
import os
import datetime as dt
from pathlib import Path
from urllib.request import Request, urlopen

CONFIG = Path.home() / '.config' / 'waybar' / 'prayer.conf'
CACHE = Path.home() / '.cache' / 'waybar-prayer.json'
GEO = Path.home() / '.cache' / 'waybar-geo.json'

DEFAULT_METHOD = 3
DEFAULT_SCHOOL = 0

PRAYERS = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']


def read_conf(path):
    cfg = {}
    if not path.is_file():
        return cfg
    with open(path) as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if not line or '=' not in line:
                continue
            k, v = line.split('=', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def write_geo(lat, lon):
    GEO.parent.mkdir(parents=True, exist_ok=True)
    with open(GEO, 'w') as f:
        f.write(f'LAT={lat}\nLON={lon}\n')


def load_or_detect_latlon(cfg):
    lat, lon = cfg.get('LAT', ''), cfg.get('LON', '')
    if lat and lon:
        return lat, lon
    if GEO.is_file():
        g = read_conf(GEO)
        lat, lon = g.get('LAT', ''), g.get('LON', '')
        if lat and lon:
            return lat, lon
    for url, latk, lonk in [
        ('https://ipapi.co/json/', 'latitude', 'longitude'),
        ('http://ip-api.com/json/', 'lat', 'lon'),
    ]:
        try:
            req = Request(url, headers={'User-Agent': 'waybar-prayer/1.0'})
            with urlopen(req, timeout=6) as r:
                data = json.loads(r.read().decode())
            lat = data.get(latk)
            lon = data.get(lonk)
            if lat and lon:
                write_geo(lat, lon)
                return lat, lon
        except Exception:
            continue
    return None, None


def fetch_json(url, timeout=15):
    req = Request(url, headers={'User-Agent': 'waybar-prayer/1.0'})
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def load_or_fetch_prayer(lat, lon, method, school):
    today_api = dt.date.today().strftime('%d-%m-%Y')
    if CACHE.is_file():
        try:
            with open(CACHE) as f:
                cached = json.load(f)
            cached_date = cached.get('data', {}).get('date', {}).get('gregorian', {}).get('date')
            if cached_date == today_api:
                return cached
        except Exception:
            pass
    try:
        url = (
            'https://api.aladhan.com/v1/timings'
            f'?latitude={lat}&longitude={lon}&method={method}&school={school}'
        )
        data = fetch_json(url)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE, 'w') as f:
            json.dump(data, f)
        return data
    except Exception:
        if CACHE.is_file():
            try:
                with open(CACHE) as f:
                    return json.load(f)
            except Exception:
                pass
        return None


def parse_time(s):
    s = s.strip().split()[0]
    parts = s.split(':')
    h, m = int(parts[0]), int(parts[1])
    sec = int(parts[2]) if len(parts) > 2 else 0
    return dt.time(h, m, sec)


def fmt12(t):
    h = t.hour % 12
    if h == 0:
        h = 12
    return f'{h}:{t.minute:02d} {"AM" if t.hour < 12 else "PM"}'


def main():
    cfg = read_conf(CONFIG)
    method = int(cfg.get('METHOD', DEFAULT_METHOD))
    school = int(cfg.get('SCHOOL', DEFAULT_SCHOOL))

    lat, lon = load_or_detect_latlon(cfg)
    if not lat or not lon:
        print(json.dumps({
            'text': 'Location?',
            'tooltip': 'Set LAT/LON in ~/.config/waybar/prayer.conf or ~/.cache/waybar-geo.json'
        }))
        return

    data = load_or_fetch_prayer(lat, lon, method, school)
    if not data:
        print(json.dumps({'text': 'No data', 'tooltip': 'Prayer API unavailable'}))
        return

    timings = data['data']['timings']
    today = dt.date.today()
    now = dt.datetime.now()

    times = [parse_time(timings[n]) for n in PRAYERS]
    dts = [dt.datetime.combine(today, t) for t in times]

    current_idx = 5
    next_idx = 0
    next_dt = dts[0] + dt.timedelta(days=1)

    for i, pt in enumerate(dts):
        if now < pt:
            next_idx = i
            current_idx = i - 1
            next_dt = pt
            break

    if current_idx < 0:
        current_idx = 5

    if next_idx == 0 and now > dts[5]:
        next_dt = dts[0] + dt.timedelta(days=1)

    current_name = PRAYERS[current_idx]
    current_time = fmt12(times[current_idx])
    next_name = PRAYERS[next_idx]
    next_time = fmt12(times[next_idx])

    remaining = next_dt - now
    total_seconds = int(remaining.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    rem_str = f'{hours}h {minutes}m' if hours else f'{minutes}m'

    schedule = '\n'.join(f'{n}: {fmt12(parse_time(timings[n]))}' for n in PRAYERS)
    tooltip = f'{current_name} {current_time} — {rem_str} until {next_name} {next_time}\n\n{schedule}'

    remaining_min = total_seconds // 60
    if 0 < remaining_min <= 30:
        bar_text = f"~{remaining_min} min left"
    else:
        bar_text = current_name

    print(json.dumps({'text': bar_text, 'tooltip': tooltip}))


if __name__ == '__main__':
    main()
