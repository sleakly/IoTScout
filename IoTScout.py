#!/usr/bin/env python3
"""
SmartDevices.py

Fast mDNS/zeroconf network scanner and interactive REPL:
 - Discovers service types, then browses each type in parallel
 - Resolves hostnames and IPv4/IPv6
 - Enriches devices in the background (MAC + vendor lookup) without blocking discovery
 - Clean, compact listing with optional Rich-powered tables
 - Modular interaction handlers for common device types

Core install:
    pip install zeroconf mac-vendor-lookup scapy rich

Notes:
 - Scapy may require admin/root privileges to send ARP requests on some platforms.
 - On Windows, scapy often requires Npcap installed (https://nmap.org/npcap/).
 - Optional integrations (Hue, Chromecast, Sonos, MQTT, HTTP, UPNP) are only needed if you plan to use their interactive prompts.
"""

from __future__ import annotations

import argparse
import time
from typing import Any, Dict, List, Optional

from zeroconf import Zeroconf

from smart_devices.discovery import (
    start_browsing,
    print_compact_table,
    get_devices,
    set_show_discoveries,
    export_devices_json,
)
from smart_devices.handlers import *  # noqa: F401,F403 - import to register handlers
from smart_devices.handlers.registry import find_handler_for_device, extract_service_name, get_registered_handlers
from smart_devices.netutils import clear_screen


# Initial scan wait time (seconds) before accepting commands
DEFAULT_INITIAL_SCAN_SECONDS = 12


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Discover smart devices on the local network')
    p.add_argument('--initial-scan', type=int, default=DEFAULT_INITIAL_SCAN_SECONDS,
                   help='Seconds to wait for initial discovery before accepting commands')
    p.add_argument('--no-wait', action='store_true',
                   help='Do not wait; immediately enter REPL while background discovery continues')
    p.add_argument('--no-clear', action='store_true', help='Do not clear the screen')
    return p.parse_args()


def _print_handlers() -> None:
    handlers = get_registered_handlers()
    if not handlers:
        print("No handlers registered.")
        return
    try:
        from rich.console import Console  # type: ignore
        from rich.table import Table  # type: ignore
        console = Console()
        table = Table(title="Available Handlers", show_lines=False)
        table.add_column("Key", no_wrap=True)
        table.add_column("Name")
        for k, v in sorted(handlers.items()):
            table.add_row(k, str(v.get('name')))
        console.print(table)
    except Exception:
        print("Available handlers:")
        for i, (k, v) in enumerate(sorted(handlers.items()), start=1):
            print(f"{i:2d}. {k:15}  - {v.get('name')}")


def main() -> None:
    args = parse_args()
    zc = Zeroconf()
    listener = start_browsing(zc)

    if not args.no_clear:
        clear_screen()

    try:
        from rich.console import Console  # type: ignore
        console = Console()
        if not args.no_wait and args.initial_scan > 0:
            console.rule("[bold]SmartDevices[/bold]")
            console.print("Searching for smart devices on the local network...\n")
        else:
            print("Searching for smart devices on the local network...")
    except Exception:
        print("Searching for smart devices on the local network...")

    # Initial scan phase
    if not args.no_wait and args.initial_scan > 0:
        try:
            from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn  # type: ignore
            with Progress(SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), transient=True) as progress:
                task = progress.add_task("Scanning...", total=args.initial_scan)
                for _ in range(args.initial_scan):
                    time.sleep(1)
                    progress.update(task, advance=1)
        except Exception:
            for remaining in range(args.initial_scan, 0, -1):
                print(f"Scanning... [{remaining:2d} seconds]", end='\r', flush=True)
                time.sleep(1)
            print(' ' * 40, end='\r')

    # Disable discovery messages after initial scan
    set_show_discoveries(False)

    if not args.no_clear:
        clear_screen()

    # Interactive REPL
    try:
        while True:
            print("\nCommands:")
            print("  l, list        - List all discovered devices")
            print("  la, listall    - Detailed list with full stored device info")
            print("  show <n>       - Show detailed info for device number <n>")
            print("  interact <n>   - Interact with device number <n> (if supported)")
            print("  scan <seconds> - Temporarily re-enable discovery output and scan again")
            print("  export <path>  - Export discovered devices to JSON")
            print("  h, handlers    - List available device handlers")
            print("  c, clear       - Clear the screen")
            print("  q, quit        - Exit the program\n")

            try:
                cmd = input("CMD> ").strip()
                time.sleep(0.05)
            except EOFError:
                continue

            if not cmd:
                continue

            if cmd in ('q', 'quit', 'exit'):
                break

            if cmd in ('c', 'clear'):
                clear_screen()
                continue

            if cmd in ('l', 'list'):
                devices = get_devices()
                devices_sorted = sorted(devices, key=lambda d: (str(d.get('friendly') or ''), str(d.get('ip') or d.get('hostname') or '')))
                print_compact_table(devices_sorted)
                continue

            if cmd in ('listall', 'la'):
                devices = get_devices()
                if not devices:
                    print("No devices discovered yet.")
                else:
                    print("\nDiscovered Devices (detailed):")
                    for i, d in enumerate(devices, start=1):
                        print('\n' + '=' * 60)
                        print(f"Device #{i}: {d.get('friendly')}")
                        for k, v in d.items():
                            if k == 'service_info':
                                continue
                            print(f"  {k}: {v}")
                    print('\n' + '=' * 60)
                continue

            if cmd.startswith('show '):
                try:
                    n = int(cmd.split(None, 1)[1]) - 1
                except Exception:
                    print("Usage: show <number>")
                    continue
                clear_screen()
                devices = get_devices()
                if n < 0 or n >= len(devices):
                    print("Invalid device number")
                    continue
                d = devices[n]
                print(f"\nDevice #{n + 1} Details:")
                print("-" * 40)
                for k, v in d.items():
                    if k == 'service_info':
                        continue
                    print(f"{k.title()}: {v}")
                continue

            if cmd.startswith('interact '):
                try:
                    n = int(cmd.split(None, 1)[1]) - 1
                except Exception:
                    print("Usage: interact <number>")
                    continue
                devices = get_devices()
                if n < 0 or n >= len(devices):
                    print("Invalid device number")
                    continue
                d = devices[n]
                handler = find_handler_for_device(d)
                if not handler:
                    short = extract_service_name(d.get('type', ''))
                    print(f"No interaction handler for service type: {short or 'unknown'}")
                    continue
                try:
                    handler['interact'](d)
                except Exception as e:
                    print(f"Handler failed: {e}")
                continue

            if cmd.startswith('scan '):
                try:
                    seconds = int(cmd.split(None, 1)[1])
                except Exception:
                    print("Usage: scan <seconds>")
                    continue
                set_show_discoveries(True)
                try:
                    from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn  # type: ignore
                    with Progress(SpinnerColumn(), *Progress.get_default_columns(), TimeElapsedColumn(), transient=True) as progress:
                        task = progress.add_task("Scanning...", total=seconds)
                        for _ in range(seconds):
                            time.sleep(1)
                            progress.update(task, advance=1)
                except Exception:
                    for remaining in range(seconds, 0, -1):
                        print(f"Scanning... [{remaining:2d} seconds]", end='\r', flush=True)
                        time.sleep(1)
                    print(' ' * 40, end='\r')
                set_show_discoveries(False)
                continue

            if cmd.startswith('export '):
                path = cmd.split(None, 1)[1].strip() if len(cmd.split(None, 1)) > 1 else ''
                if not path:
                    print("Usage: export <path>")
                    continue
                try:
                    export_devices_json(path)
                except Exception as e:
                    print(f"Export failed: {e}")
                continue

            if cmd in ('handlers', 'h'):
                _print_handlers()
                continue

            print("Commands: list, show <n>, interact <n>, handlers, scan <s>, export <path>, quit")
    except KeyboardInterrupt:
        pass
    finally:
        try:
            zc.close()
        except Exception:
            pass
        print("Exiting.")


if __name__ == "__main__":
    main()