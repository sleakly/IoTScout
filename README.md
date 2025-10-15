
# IoTScout

IoTScout is a fast, modular tool for discovering and interacting with smart devices (IoT) on your local network. It uses mDNS/zeroconf to find devices, enriches their information, and provides interactive prompts for device-specific actions.

## Features
- **Network scanning:** Discovers all mDNS service types and browses each for devices in parallel.
- **Device enrichment:** Resolves hostnames, IP addresses, MAC addresses, and vendor info.
- **Interactive REPL:** Lets you interact with discovered devices using modular handlers (Chromecast, Hue, Sonos, MQTT, HTTP, UPNP, etc.).
- **Extensible:** Easily add new device handlers for other protocols or device types.
- **Rich output:** Optionally displays results in formatted tables using the Rich library.

## Installation
Install required packages:

```sh
pip install zeroconf mac-vendor-lookup scapy rich
```

Optional integrations (install as needed):
- `pychromecast` for Chromecast
- `phue` for Philips Hue
- `soco` for Sonos
- `paho-mqtt` for MQTT
- `requests` for HTTP
- `upnpy` for UPnP

## Usage
Run the main script:

```sh
python IoTScout.py
```

Command-line options:
- `--initial-scan <seconds>`: Wait time for initial device discovery
- `--no-wait`: Enter REPL immediately while background discovery continues
- `--no-clear`: Do not clear the screen before displaying results

## Notes
- Scapy may require admin/root privileges for ARP requests.
- On Windows, Scapy often requires Npcap installed (https://nmap.org/npcap/).
- Optional integrations are only needed for their respective device handlers.

## Project Structure
- `IoTScout.py`: Main entry point
- `smart_devices/`: Device discovery, network utilities, and handlers
- `requirements.txt`: List of required Python packages

## License
MIT