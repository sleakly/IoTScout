from __future__ import annotations

import re
import socket
import subprocess
import sys
import threading
from functools import lru_cache
from typing import Optional

try:
    from scapy.all import getmacbyip  # type: ignore
    _HAS_SCAPY = True
except Exception:
    _HAS_SCAPY = False

try:
    from mac_vendor_lookup import MacLookup  # type: ignore
    _HAS_MACLOOKUP = True
except Exception:
    _HAS_MACLOOKUP = False

_MACLOOK: Optional[MacLookup] = None
_MACLOOK_INIT_LOCK = threading.Lock()


def format_mac(mac_raw: str) -> str:
    if not mac_raw:
        return ''
    mac = mac_raw.strip().replace('-', ':').replace('.', ':').upper()
    if re.fullmatch(r'[0-9A-F]{12}', mac):
        mac = ':'.join(mac[i:i + 2] for i in range(0, 12, 2))
    return mac


def _get_maclookup() -> Optional[MacLookup]:
    global _MACLOOK
    if not _HAS_MACLOOKUP:
        return None
    if _MACLOOK is None:
        with _MACLOOK_INIT_LOCK:
            if _MACLOOK is None:
                try:
                    _MACLOOK = MacLookup()
                    if hasattr(_MACLOOK, '_load_vendors'):
                        try:
                            _MACLOOK._load_vendors()  # type: ignore[attr-defined]
                        except Exception:
                            pass
                except Exception:
                    _MACLOOK = None
    return _MACLOOK


def _arp_lookup_os(ip: str) -> str:
    try:
        if sys.platform.startswith('win'):
            result = subprocess.check_output(['arp', '-a'], encoding='utf8', errors='ignore')
            pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F\-\:]{11,17})')
        else:
            result = subprocess.check_output(['arp', '-a'], encoding='utf8', errors='ignore')
            pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+).+(?:at|HWaddr)\s+([0-9a-fA-F\:\-]{11,17})')
        for m in pattern.finditer(result):
            ip_found, mac = m.groups()
            if ip_found == ip:
                return format_mac(mac)
    except Exception:
        pass
    return ''


def _ping_once(ip: str) -> None:
    try:
        if sys.platform.startswith('win'):
            subprocess.run(['ping', '-n', '1', '-w', '1000', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['ping', '-c', '1', '-W', '1', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


@lru_cache(maxsize=4096)
def get_mac_for_ip(ip: str) -> str:
    if not ip:
        return ''
    if _HAS_SCAPY:
        try:
            guessed = getmacbyip(ip)
            if guessed:
                mac = format_mac(guessed)
                if mac:
                    return mac
        except Exception:
            pass
    mac = _arp_lookup_os(ip)
    if mac:
        return mac
    _ping_once(ip)
    return _arp_lookup_os(ip)


@lru_cache(maxsize=4096)
def get_vendor_for_mac(mac: str) -> str:
    if not mac or not _HAS_MACLOOKUP:
        return ''
    try:
        m = _get_maclookup()
        if not m:
            return ''
        vendor = m.lookup(mac)
        return vendor or ''
    except Exception:
        try:
            m = _get_maclookup()
            if not m:
                return ''
            m.update_vendors()
            vendor = m.lookup(mac)
            return vendor or ''
        except Exception:
            return ''


def clear_screen() -> None:
    try:
        if sys.platform.startswith('win'):
            _ = subprocess.call('cls', shell=True)
        else:
            _ = subprocess.call('clear', shell=True)
    except Exception:
        pass
