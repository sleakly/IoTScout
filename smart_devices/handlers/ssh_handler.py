from __future__ import annotations

from .registry import register_device_handler


def _generic_ssh_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    print(f"SSH service detected for {ip}. To connect use: ssh <user>@{ip}")


register_device_handler('ssh', {'name': 'SSH Service', 'interact': _generic_ssh_interact})
