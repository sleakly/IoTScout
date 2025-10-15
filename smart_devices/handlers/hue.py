from __future__ import annotations

from typing import Any

from .registry import register_device_handler

try:
    from phue import Bridge  # type: ignore
    _HAS_PHUE = True
except Exception:
    _HAS_PHUE = False


def _resolve_hue_target(target: str, lights_map: dict) -> str:
    if not target:
        raise ValueError("Empty target")
    if target.isdigit():
        idx = int(target) - 1
        names = list(lights_map.keys())
        if idx < 0 or idx >= len(names):
            raise IndexError("index out of range")
        return names[idx]
    if target in lights_map:
        return target
    for n in lights_map.keys():
        if n.lower() == target.lower():
            return n
    for n in lights_map.keys():
        if target.lower() in n.lower():
            return n
    raise LookupError(f"No light matching: {target}")


def hue_command_loop(bridge: 'Bridge') -> None:
    try:
        lights_map = bridge.get_light_objects('name')
    except Exception:
        lights_map = {}
    print("Connected to Hue bridge. Lights:")
    for i, name in enumerate(lights_map.keys(), start=1):
        print(f"  {i}. {name}")
    print("\nCommands: list | on <id|name> | off <id|name> | toggle <id|name> | bri <id|name> <0-254> | hue <id|name> <0-65535> | sat <id|name> <0-254> | quit")
    while True:
        try:
            cmd = input("hue> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd:
            continue
        parts = cmd.split()
        op = parts[0].lower()
        try:
            if op in ('q', 'quit', 'exit'):
                break
            if op in ('list', 'ls'):
                try:
                    lights_map = bridge.get_light_objects('name')
                except Exception:
                    lights_map = {}
                for i, name in enumerate(lights_map.keys(), start=1):
                    print(f"  {i}. {name}")
                continue
            if op in ('on', 'off', 'toggle'):
                if len(parts) < 2:
                    print("Usage: on|off|toggle <id|name>")
                    continue
                target = _resolve_hue_target(parts[1], lights_map)
                if op == 'on':
                    bridge.set_light(target, 'on', True)
                elif op == 'off':
                    bridge.set_light(target, 'on', False)
                else:
                    state = bridge.get_light(target)['state']['on']
                    bridge.set_light(target, 'on', not state)
                print(f"{op} -> {target}")
                continue
            if op in ('bri', 'brightness'):
                if len(parts) < 3:
                    print("Usage: bri <id|name> <0-254>")
                    continue
                target = _resolve_hue_target(parts[1], lights_map)
                bri = int(parts[2])
                bri = max(0, min(254, bri))
                bridge.set_light(target, 'bri', bri)
                print(f"Set brightness {target} -> {bri}")
                continue
            if op == 'hue':
                if len(parts) < 3:
                    print("Usage: hue <id|name> <0-65535>")
                    continue
                target = _resolve_hue_target(parts[1], lights_map)
                h = int(parts[2])
                h = max(0, min(65535, h))
                bridge.set_light(target, 'hue', h)
                print(f"Set hue {target} -> {h}")
                continue
            if op in ('sat', 'saturation'):
                if len(parts) < 3:
                    print("Usage: sat <id|name> <0-254>")
                    continue
                target = _resolve_hue_target(parts[1], lights_map)
                s = int(parts[2])
                s = max(0, min(254, s))
                bridge.set_light(target, 'sat', s)
                print(f"Set saturation {target} -> {s}")
                continue
            print("Unknown command")
        except Exception as e:
            print("Error:", e)


def _hue_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    if not ip:
        print("No IP/hostname available for Hue device.")
        return
    if not _HAS_PHUE:
        print("To interact with Philips Hue bridges install 'phue' package: pip install phue")
        return
    try:
        b = Bridge(ip)  # type: ignore[operator]
        b.connect()
        print(f"Connected to Hue bridge at {ip}. Entering interactive Hue prompt...")
        hue_command_loop(b)
    except Exception as e:
        print(f"Failed to interact with Hue bridge at {ip}: {e}")


register_device_handler('hue', {'name': 'Philips Hue', 'interact': _hue_interact})
