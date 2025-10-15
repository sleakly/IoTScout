from __future__ import annotations

import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo

from .handlers.registry import extract_service_name
from .netutils import get_mac_for_ip, get_vendor_for_mac

try:
    from rich.console import Console  # type: ignore
    from rich.table import Table  # type: ignore
    _HAS_RICH = True
    _console = Console()
except Exception:
    _HAS_RICH = False
    _console = None  # type: ignore


SERVICE_SUFFIX_TO_NAME: Dict[str, str] = {
    '_googlecast._tcp.local.': 'Google Cast (Chromecast/Google Home)',
    '_hue._tcp.local.': 'Philips Hue Bridge',
    '_hap._tcp.local.': 'Apple HomeKit Accessory (HAP)',
    '_airplay._tcp.local.': 'Apple AirPlay / AppleTV',
    '_spotify-connect._tcp.local.': 'Spotify Connect',
    '_http._tcp.local.': 'HTTP Web Service',
    '_https._tcp.local.': 'HTTPS Web Service',
    '_ssh._tcp.local.': 'SSH Service',
    '_ipp._tcp.local.': 'IPP Printer',
    '_printer._tcp.local.': 'Network Printer',
    '_scanner._tcp.local.': 'Network Scanner',
    '_amzn-wplay._tcp.local.': 'Amazon Fire / Alexa',
    '_androidtvremote2._tcp.local.': 'Android TV Remote',
    '_companion-link._tcp.local.': 'Companion Link / Phone Link',
    '_carplay-ctrl._tcp.local.': 'Apple CarPlay Control',
    '_spotify-social-listening._tcp.local.': 'Spotify Social Listening',
    '_sonos._tcp.local.': 'Sonos',
    '_matter._tcp.local.': 'Matter Smart Home Device',
}

SERVICE_TYPE_NAMES: Dict[str, str] = {
    'googlecast': 'Google Cast (Chromecast/Google Home)',
    'googlecast-tls': 'Google Cast (secure)',
    'hue': 'Philips Hue Bridge',
    'philipshue': 'Philips Hue Bridge',
    'airplay': 'Apple AirPlay / AppleTV',
    'airplay2': 'Apple AirPlay 2',
    'raop': 'AirPlay (RAOP)',
    'raopv2': 'AirPlay (RAOP v2)',
    'homekit': 'Apple HomeKit Accessory',
    'hap': 'Apple HomeKit Accessory (HAP)',
    'amzn-alexa': 'Amazon Alexa / Echo',
    'amzn-wplay': 'Amazon Fire TV / Alexa Cast',
    'sonos': 'Sonos Speaker',
    'spotify-connect': 'Spotify Connect',
    'spotify': 'Spotify Service',
    'roku': 'Roku Device',
    'androidtv': 'Android TV',
    'androidtvremote2': 'Android TV Remote',
    'chromecast': 'Chromecast',
    'dlna': 'DLNA Media Server / Renderer',
    'ipp': 'IPP Printer',
    'printer': 'Network Printer',
    'pdl-datastream': 'Printer (PDL datastream)',
    'scanner': 'Network Scanner',
    'uscan': 'Scanner',
    'privet': 'Cloud Print / Privet Printer',
    'home-assistant': 'Home Assistant',
    'mqtt': 'MQTT Broker',
    'mqtt-tls': 'MQTT Broker (TLS)',
    'tplink': 'TP-Link Smart Device',
    'tplink-https': 'TP-Link (HTTPS)',
    'aqara-setup': 'Aqara Setup / Hub',
    'aqara': 'Aqara device',
    'matter': 'Matter Smart Home Device',
    'hap-ble': 'HAP over BLE (HomeKit)',
    'http': 'HTTP Web Service',
    'https': 'HTTPS Web Service',
    'ssh': 'SSH Service',
    'ftp': 'FTP Service',
    'smb': 'SMB / Windows Share',
    'afpovertcp': 'Apple Filing Protocol (AFP)',
    'smbd': 'SMB',
    'googlezone': 'Google Zone / Cast',
    'apple-mobdev2': 'Apple Mobile Device',
    'companion-link': 'Companion Link / Phone Link',
    'carplay-ctrl': 'Apple CarPlay Control',
    'http-alt': 'Alternate HTTP',
    'cros-p2p': 'ChromeOS P2P service (Chromebook)',
}


EXECUTOR = ThreadPoolExecutor(max_workers=8)
_discovered_lock = threading.Lock()
_discovered: set[Tuple[str, str]] = set()
_browsed_types_lock = threading.Lock()
_browsed_types: set[str] = set()

_discovered_devices_lock = threading.Lock()
_discovered_devices: List[Dict[str, Any]] = []

_show_discoveries = True
_show_discoveries_lock = threading.Lock()


def get_devices() -> List[Dict[str, Any]]:
    with _discovered_devices_lock:
        return list(_discovered_devices)


def set_show_discoveries(value: bool) -> None:
    global _show_discoveries
    with _show_discoveries_lock:
        _show_discoveries = value


def _print_discovery_line(idx: int, device: Dict[str, Any]) -> None:
    friendly = device.get('friendly') or extract_service_name(device.get('type', '')) or 'Device'
    type_ = device.get('type') or ''
    name = device.get('name') or ''
    host = device.get('hostname') or ''
    ip = device.get('ip') or ''
    mac = device.get('mac') or ''
    vendor = device.get('vendor') or ''

    if _HAS_RICH and _console:
        pieces = [f"[{idx}] {friendly}"]
        detail = []
        if ip: detail.append(f"IP: {ip}")
        if host: detail.append(f"Host: {host}")
        if mac: detail.append(f"MAC: {mac}")
        if vendor: detail.append(f"Vendor: {vendor}")
        if type_: detail.append(f"Type: {type_}")
        if name: detail.append(f"Name: {name}")
        _console.print(" • ".join(pieces + detail))
    else:
        parts = [f"[{idx}] {friendly}"]
        if ip: parts.append(f"IP: {ip}")
        if host: parts.append(f"Host: {host}")
        if mac: parts.append(f"MAC: {mac}")
        if vendor: parts.append(f"Vendor: {vendor}")
        parts.append(f"Service: {type_}")
        parts.append(f"Name: {name}")
        print(" | ".join(parts), flush=True)


def _enrich_device_mac_vendor(device_index: int) -> None:
    with _discovered_devices_lock:
        if device_index < 0 or device_index >= len(_discovered_devices):
            return
        device = _discovered_devices[device_index]
    ip = device.get('ip') or ''
    if not ip:
        return
    mac = get_mac_for_ip(ip)
    vendor = get_vendor_for_mac(mac) if mac else ''
    updated = False
    with _discovered_devices_lock:
        d = _discovered_devices[device_index]
        if mac and not d.get('mac'):
            d['mac'] = mac
            updated = True
        if vendor and not d.get('vendor'):
            d['vendor'] = vendor
            updated = True
    if updated:
        with _show_discoveries_lock:
            if _show_discoveries:
                _print_discovery_line(device_index + 1, d)


class Listener:
    def remove_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        key = (type, name)
        with _discovered_lock:
            if key in _discovered:
                _discovered.remove(key)

    def update_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        self.add_service(zeroconf, type, name)

    def add_service(self, zeroconf: Zeroconf, type: str, name: str) -> None:
        if type == "_services._dns-sd._udp.local.":
            service_type = name
            if not service_type.endswith('.local.'):
                if service_type.endswith('.local'):
                    service_type += '.'
                else:
                    service_type += '.local.'
            with _browsed_types_lock:
                if service_type in _browsed_types:
                    return
                _browsed_types.add(service_type)
            try:
                ServiceBrowser(zeroconf, service_type, self)
            except Exception:
                return
            return

        key = (type, name)
        with _discovered_lock:
            if key in _discovered:
                return
            _discovered.add(key)

        try:
            info = zeroconf.get_service_info(type, name, timeout=2500)  # type: Optional[ServiceInfo]
        except Exception:
            return

        if not info:
            friendly = SERVICE_SUFFIX_TO_NAME.get(type) or SERVICE_TYPE_NAMES.get(extract_service_name(type)) or f"{extract_service_name(type)} (service)"
            device = {
                'type': type,
                'name': name,
                'friendly': friendly,
                'hostname': '',
                'ip': '',
                'mac': '',
                'vendor': '',
                'service_info': None,
                'properties': {},
            }
            with _discovered_devices_lock:
                _discovered_devices.append(device)
                idx = len(_discovered_devices)
            with _show_discoveries_lock:
                if _show_discoveries:
                    _print_discovery_line(idx, device)
            return

        hostname = (info.server or '').rstrip('.')
        try:
            parsed_addrs = info.parsed_addresses()
        except Exception:
            parsed_addrs = []
            try:
                for a in info.addresses:
                    if len(a) == 4:
                        import socket as _s
                        parsed_addrs.append(_s.inet_ntoa(a))
                    elif len(a) == 16:
                        parsed_addrs.append(_s.inet_ntop(_s.AF_INET6, a))
            except Exception:
                pass

        ip_v4 = ''
        ip_v6 = ''
        for addr in parsed_addrs:
            if ':' in addr:
                ip_v6 = addr
            else:
                ip_v4 = addr
                break

        decoded_props: Dict[str, Any] = {}
        try:
            for k, v in (info.properties or {}).items():
                try:
                    dk = k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
                    if isinstance(v, (bytes, bytearray)):
                        try:
                            dv = v.decode()
                        except Exception:
                            dv = str(v)
                    else:
                        dv = v
                    decoded_props[dk] = dv
                except Exception:
                    pass
        except Exception:
            decoded_props = {}

        friendly = SERVICE_SUFFIX_TO_NAME.get(type) or SERVICE_TYPE_NAMES.get(extract_service_name(type))
        if not friendly:
            props = decoded_props
            friendly = props.get('fn') or props.get('name') or f"{extract_service_name(type)} (service)"

        device = {
            'type': type,
            'name': name,
            'friendly': friendly,
            'hostname': hostname,
            'ip': ip_v4 or ip_v6 or '',
            'mac': '',
            'vendor': '',
            'service_info': info,
            'properties': decoded_props,
        }
        with _discovered_devices_lock:
            _discovered_devices.append(device)
            idx = len(_discovered_devices)

        with _show_discoveries_lock:
            if _show_discoveries:
                _print_discovery_line(idx, device)

        if device['ip']:
            EXECUTOR.submit(_enrich_device_mac_vendor, idx - 1)


def print_compact_table(devices: List[Dict[str, Any]]) -> None:
    if _HAS_RICH and _console:
        from rich.table import Table  # type: ignore
        table = Table(title="Discovered Devices", show_lines=False)
        table.add_column("#", justify="right", no_wrap=True)
        table.add_column("Friendly", overflow="fold", max_width=40)
        table.add_column("Address", overflow="fold", max_width=40)
        for i, d in enumerate(devices, start=1):
            friendly = str(d.get('friendly') or '')
            addr = str(d.get('ip') or d.get('hostname') or '')
            table.add_row(str(i), friendly, addr)
        _console.print(table)
    else:
        print("\nDiscovered Devices (short):")
        print(f"{'#':>3}  {'Friendly':30}  {'Address':20}")
        print('-' * 70)
        for i, d in enumerate(devices, start=1):
            friendly = str(d.get('friendly') or '')
            addr = str(d.get('ip') or d.get('hostname') or '')
            if len(friendly) > 30:
                friendly = friendly[:27] + '...'
            if len(addr) > 20:
                addr = addr[:17] + '...'
            print(f"{i:3d}. {friendly:30}  {addr:20}")


def export_devices_json(path: str) -> None:
    with _discovered_devices_lock:
        data = [
            {k: (v if k != 'service_info' else None) for k, v in d.items()}
            for d in _discovered_devices
        ]
    import json
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Exported {len(data)} devices to {path}")


def start_browsing(zc: Zeroconf) -> Listener:
    listener = Listener()
    ServiceBrowser(zc, "_services._dns-sd._udp.local.", listener)
    return listener
