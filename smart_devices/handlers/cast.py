from __future__ import annotations

from .registry import register_device_handler

try:
    import pychromecast  # type: ignore
    _HAS_PYCHROMECAST = True
except Exception:
    _HAS_PYCHROMECAST = False


def _cast_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    if not ip:
        print('No IP/hostname available for Chromecast device.')
        return
    if not _HAS_PYCHROMECAST:
        print('pychromecast not installed; pip install pychromecast')
        return
    try:
        cc = pychromecast.Chromecast(ip)  # type: ignore[call-arg]
        cc.wait()
        print('Commands: status | quit')
        while True:
            try:
                cmd = input('cast> ').strip()
            except (EOFError, KeyboardInterrupt):
                print(); break
            if not cmd:
                continue
            if cmd in ('q', 'quit', 'exit'):
                break
            if cmd == 'status':
                try:
                    print(cc.status)
                except Exception as e:
                    print('status failed:', e)
                continue
            print('Unknown command')
    except Exception as e:
        print(f'Chromecast interaction failed: {e}')


register_device_handler('googlecast', {'name': 'Google Chromecast', 'interact': _cast_interact})
register_device_handler('chromecast', {'name': 'Google Chromecast', 'interact': _cast_interact})
