from __future__ import annotations

import socket
from typing import List

from .registry import register_device_handler


def printer_command_loop(ip: str) -> None:
    print(f"Printer interactive prompt for {ip}")
    print("Commands: listinfo | print | raw <text> | sendfile <path> | quit")
    while True:
        try:
            cmd = input('printer> ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd:
            continue
        parts = cmd.split(None, 2)
        op = parts[0].lower()
        try:
            if op in ('q', 'quit', 'exit'):
                break
            if op == 'listinfo':
                print(f'Printer IP: {ip}')
                continue
            if op == 'print':
                print('Enter text to print. End with blank line:')
                lines: List[str] = []
                while True:
                    try:
                        line = input()
                    except (EOFError, KeyboardInterrupt):
                        print('\nCancelled')
                        lines = []
                        break
                    if line == '':
                        break
                    lines.append(line)
                if not lines:
                    print('No text to print')
                    continue
                payload = '\n'.join(lines) + '\n'
                print('Select method: 1) raw TCP 2) HTTP POST')
                choice = (input('Method [1/2]: ').strip() or '1')
                if choice == '1':
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(5)
                        s.connect((ip, 9100))
                        s.sendall(payload.encode('utf-8', errors='replace'))
                        try:
                            s.sendall(b'\f')
                        except Exception:
                            pass
                        s.close()
                        print('Sent text to printer via raw TCP (9100).')
                    except Exception as e:
                        print(f'Raw TCP print failed: {e}')
                else:
                    try:
                        import requests  # type: ignore
                        r = requests.post(f'http://{ip}/', data={'text': payload}, timeout=5)  # type: ignore[operator]
                        print(f'HTTP POST returned {r.status_code}')
                    except Exception as e:
                        print(f'HTTP print failed: {e}')
                continue
            if op == 'raw':
                if len(parts) < 2:
                    print('Usage: raw <text>')
                    continue
                text = parts[1] if len(parts) == 2 else parts[1] + ' ' + parts[2]
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((ip, 9100))
                    s.sendall(text.encode('utf-8', errors='replace'))
                    try:
                        s.sendall(b'\f')
                    except Exception:
                        pass
                    s.close()
                    print('Sent raw text to printer.')
                except Exception as e:
                    print(f'Raw send failed: {e}')
                continue
            if op == 'sendfile':
                if len(parts) < 2:
                    print('Usage: sendfile <path>')
                    continue
                path = parts[1]
                try:
                    with open(path, 'rb') as fh:
                        data = fh.read()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect((ip, 9100))
                    s.sendall(data)
                    s.close()
                    print('Sent file bytes to printer.')
                except Exception as e:
                    print(f'Sendfile failed: {e}')
                continue
            print('Unknown printer command')
        except Exception as e:
            print('Error:', e)


def _printer_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    if not ip:
        print('No IP/hostname available for printer.')
        return
    try:
        printer_command_loop(ip)
    except Exception as e:
        print(f'Printer interaction failed: {e}')


register_device_handler('printer', {'name': 'Network Printer (print text)', 'interact': _printer_interact})
register_device_handler('ipp', {'name': 'IPP Printer', 'interact': _printer_interact})
