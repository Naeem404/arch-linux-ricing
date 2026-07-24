#!/usr/bin/env python3
import json
import subprocess
import sys

action = sys.argv[1] if len(sys.argv) > 1 else "off"

try:
    raw = subprocess.check_output(["niri", "msg", "-j", "outputs"])
    outputs = json.loads(raw)
except Exception:
    outputs = {}

for name in outputs:
    subprocess.run(["niri", "msg", "output", name, action], check=False)
