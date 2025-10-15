from __future__ import annotations

from .registry import register_device_handler


def _matter_interact(device: dict) -> None:
    print("Matter device discovered. Matter interactions require a controller/sdk; see docs.")


register_device_handler('matter', {'name': 'Matter Device', 'interact': _matter_interact})
