from __future__ import annotations

from .registry import register_device_handler

try:
    import paho.mqtt.client as mqtt  # type: ignore
    _HAS_PAHO = True
except Exception:
    _HAS_PAHO = False


def mqtt_command_loop(ip: str) -> None:
    print(f"MQTT interactive prompt for broker {ip}")
    print("Commands: publish <topic> <message> | quit")
    if not _HAS_PAHO:
        print('paho-mqtt not installed; install with: pip install paho-mqtt')
        return
    while True:
        try:
            cmd = input('mqtt> ').strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not cmd:
            continue
        parts = cmd.split(None, 2)
        if parts[0] in ('q', 'quit', 'exit'):
            break
        if parts[0] == 'publish':
            if len(parts) < 3:
                print('Usage: publish <topic> <message>')
                continue
            topic = parts[1]
            msg = parts[2]
            try:
                client = mqtt.Client()
                client.connect(ip, 1883, 5)
                client.loop_start()
                client.publish(topic, msg)
                import time
                time.sleep(0.3)
                client.loop_stop()
                client.disconnect()
                print(f'Published to {topic}')
            except Exception as e:
                print('Publish failed:', e)
            continue
        print('Unknown command')


def _mqtt_interact(device: dict) -> None:
    ip = device.get('ip') or device.get('hostname')
    if not ip:
        print('No IP/hostname available for MQTT broker.')
        return
    try:
        mqtt_command_loop(ip)
    except Exception as e:
        print(f'MQTT interaction failed: {e}')


register_device_handler('mqtt', {'name': 'MQTT Broker', 'interact': _mqtt_interact})
