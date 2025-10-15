from __future__ import annotations

from typing import Any, Dict, Optional

# Central registry for device interaction handlers keyed by service short-name
_device_handlers: Dict[str, Dict[str, Any]] = {}


def extract_service_name(type_str: str) -> str:
    """Extract short service name from a type string like '_hue._tcp.local.' -> 'hue'"""
    if not type_str:
        return ''
    t = type_str
    if t.startswith('_'):
        t = t[1:]
    parts = t.split('._')
    if parts:
        name = parts[0]
        name = name.replace('.local.', '').replace('.local', '')
        return name.lower()
    return t.lower()


def register_device_handler(key: str, handler: dict) -> None:
    """Register a device interaction handler.

    handler must have:
      - 'name': human-friendly handler name
      - 'interact': callable(device_dict) -> None
    """
    _device_handlers[key] = handler


def get_registered_handlers() -> Dict[str, Dict[str, Any]]:
    return dict(_device_handlers)


def find_handler_for_device(device: dict) -> Optional[dict]:
    """Find a suitable handler for a device using multiple strategies."""
    svc_type = device.get('type', '')
    short = extract_service_name(svc_type)
    if short in _device_handlers:
        return _device_handlers[short]
    # Match by TXT properties
    props = device.get('properties', {}) or {}
    for key, val in props.items():
        k = str(key).lower()
        v = str(val).lower()
        if 'matter' in (k + v) and 'matter' in _device_handlers:
            return _device_handlers['matter']
        if ('homeassistant' in (k + v) or 'hass' in (k + v)) and 'home-assistant' in _device_handlers:
            return _device_handlers['home-assistant']
    # Substring match in friendly or name
    friendly = (device.get('friendly') or '').lower()
    name = (device.get('name') or '').lower()
    for k in _device_handlers.keys():
        if k in friendly or k in name:
            return _device_handlers[k]
    return None
