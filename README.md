# FlooCast

A Python application for configuring and controlling FlooGoo USB Bluetooth dongles (FMA120) on Debian/Ubuntu Linux.

Features:
- Pair and connect with Bluetooth headsets/speakers
- Stream audio and make VoIP calls
- AuraCast broadcast functionality

The dongle functions as a standard USB audio device requiring no drivers.

## Prerequisites

Install system dependencies:

```bash
sudo apt update
sudo apt install python3-dev python3-wxgtk4.0 libsndfile1 gir1.2-appindicator3-0.1
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

Clone the repository and sync dependencies:

```bash
git clone <repo-url>
cd FlooCast
uv sync
```

## Running

```bash
uv run python main.py
```

## USB Permissions

If you see "Permission denied: '/dev/ttyACM0'", add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and log back in for the change to take effect.

Alternatively, run as root:

```bash
sudo uv run python main.py
```

## Building .deb Package

To build a Debian package:

```bash
sudo apt install debhelper devscripts
dpkg-buildpackage -us -uc -b
```

The package will be created in the parent directory.

## Installing .deb Package

```bash
sudo apt install ./floocast_*.deb
```

Using `apt install` (not `dpkg -i`) ensures dependencies are automatically resolved.

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
