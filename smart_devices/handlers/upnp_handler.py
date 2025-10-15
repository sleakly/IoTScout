from __future__ import annotations

from .registry import register_device_handler

try:
    import upnpy  # type: ignore
    _HAS_UPNPY = True
except Exception:
    _HAS_UPNPY = False


def _upnp_interact(device: dict) -> None:
    if not _HAS_UPNPY:
        print('Install upnpy: pip install upnpy')
        return
    ip = device.get('ip') or device.get('hostname') or ''
    try:
        u = upnpy.UPnP()  # type: ignore[attr-defined]
        _ = u.discover()
        print(f'UPnP discovery attempted near {ip}.')
    except Exception as e:
        print(f'UPnP interaction failed: {e}')


register_device_handler('upnp', {'name': 'UPnP/SSDP Device', 'interact': _upnp_interact})
