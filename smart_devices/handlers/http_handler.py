from __future__ import annotations

from .registry import register_device_handler

try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False


def http_command_loop(ip: str) -> None:
    print(f"HTTP interactive prompt for {ip}")
    print("Commands: get <path> | post <path> <data> | quit")
    if not _HAS_REQUESTS:
        print('requests not installed; install with: pip install requests')
        return
    base = f'http://{ip}'
    while True:
        try:
            cmd = input('http> ').strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not cmd:
            continue
        parts = cmd.split(None, 2)
        if parts[0] in ('q', 'quit', 'exit'):
            break
        if parts[0] == 'get':
            path = parts[1] if len(parts) > 1 else '/'
            try:
                r = requests.get(base + path, timeout=5)  # type: ignore[operator]
                print(f'{r.status_code} {r.headers.get("content-type")}')
                print(r.text[:1000])
            except Exception as e:
                print('GET failed:', e)
            continue
        if parts[0] == 'post':
            if len(parts) < 3:
                print('Usage: post <path> <data>')
                continue
            path = parts[1]
            data = parts[2]
            try:
                r = requests.post(base + path, data=data.encode('utf-8'), timeout=5)  # type: ignore[operator]
                print(f'{r.status_code} {r.text[:400]}')
            except Exception as e:
                print('POST failed:', e)
            continue
        print('Unknown command')


def _http_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    if not ip:
        print('No IP/hostname available for HTTP service.')
        return
    try:
        http_command_loop(ip)
    except Exception as e:
        print(f'HTTP interaction failed: {e}')


register_device_handler('http', {'name': 'HTTP Service', 'interact': _http_interact})
register_device_handler('https', {'name': 'HTTP Service (HTTPS)', 'interact': _http_interact})
