from __future__ import annotations

from .registry import register_device_handler

try:
    import soco  # type: ignore
    _HAS_SOCO = True
except Exception:
    _HAS_SOCO = False


def _sonos_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    if not ip:
        print('No IP/hostname available for Sonos device.')
        return
    if not _HAS_SOCO:
        print('soco not installed; pip install soco')
        return
    try:
        speaker = soco.SoCo(ip)  # type: ignore[attr-defined]
    except Exception as e:
        print('Failed to connect to Sonos:', e); return
    print('Commands: info | current | play | pause | stop | quit')
    while True:
        try:
            cmd = input('sonos> ').strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not cmd:
            continue
        if cmd in ('q', 'quit', 'exit'):
            break
        if cmd == 'info':
            try:
                print(speaker.get_speaker_info())
            except Exception as e:
                print('info failed:', e)
            continue
        if cmd == 'current':
            try:
                print(speaker.get_current_track_info())
            except Exception as e:
                print('current failed:', e)
            continue
        if cmd == 'play':
            try: speaker.play()
            except Exception as e: print('play failed:', e)
            continue
        if cmd == 'pause':
            try: speaker.pause()
            except Exception as e: print('pause failed:', e)
            continue
        if cmd == 'stop':
            try: speaker.stop()
            except Exception as e: print('stop failed:', e)
            continue
        print('Unknown command')


register_device_handler('sonos', {'name': 'Sonos', 'interact': _sonos_interact})
