from __future__ import annotations

from .registry import register_device_handler


def _home_assistant_interact(device: dict) -> None:
    print("Home Assistant device discovered:")
    for k, v in (device.get('properties') or {}).items():
        print(f"  {k}: {v}")


register_device_handler('home-assistant', {'name': 'Home Assistant', 'interact': _home_assistant_interact})
