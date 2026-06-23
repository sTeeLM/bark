# Bark Notifier

A system-wide Python notification library and CLI tool for Bark (iOS Push Notification App). Supports advanced V2 API features including custom icons, redirection URLs, time-to-live expiration, multi-mode AES encryption, and automated Systemd/Logrotate integration.

## Directory Structure

```text
bark-project/
├── pyproject.toml
├── bark.conf
└── src/
    └── bark_notifier/
        ├── __init__.py
        ├── core.py
        └── cli.py
```

## Features

- **Subcommand Syntax**: Implements strict `bark-cli [send|delete]` layout with robust parameter boundary validation.
- **End-to-End Encryption**: Leverages native OpenSSL subsystems for AES-128, AES-192, and AES-256 ciphers across CBC, ECB, and GCM mechanisms.
- **Dynamic Diagnostics**: Provides a granular `--verbose` switch to safely intercept and print full JSON outbound/inbound payloads.
- **Automatic Timezone Prefix**: Appends localized high-precision uppercase server runtime zone tags (`[CST ...]`, `[UTC ...]`) seamlessly.

## Configuration

Place your primary settings file at `/etc/bark/bark.conf`.

```ini
[DEFAULT]
key = your_private_device_key
server = https://day.app
title = Server Alert
group = Infrastructure
sound = alarm
level = time_sensitive
timestamp = true

encryption = true
encryption_key = your_32_byte_aes_key_here_____
iv = your_16_byte_initialization_v
encryption_algorithm = aes256
encryption_mechanism = cbc
```

## Installation

Compile and install the distribution wheel package onto your host system environment:

```bash
# Clean previous artifacts
rm -rf build/ dist/ src/*.egg-info/

# Compile the wheel package
python3 -m build

# Force install globally
sudo pip install --force-reinstall dist/bark_notifier-0.1.1-py3-none-any.whl
```

## CLI Usage

### 1. Send Notifications
```bash
# Standard dispatch using configuration defaults
bark-cli send "Database storage checkpoint completed."

# High-priority alert with custom sound and critical override
bark-cli send "RAID partition degraded!" -t "Hardware Alert" -l critical -s alarm --call

# Send with localized tracking ID and full network telemetry output
bark-cli send "Microservice container failed." --id "job_99" -v
```

### 2. Recall Notifications
```bash
# Erase a specific notification card from the iOS device history interface
bark-cli delete "job_99"
```

## Python API Usage

```python
from bark_notifier import BarkNotifier

# Instantiates automatically by evaluating /etc/bark/bark.conf
notifier = BarkNotifier()

# Basic payload execution
notifier.send(body="System inspection passed.")

# Advanced context override invocation
notifier.send(
    body="Critical emergency!",
    title="Core Failure",
    level="critical",
    call=True,
    sound="alarm"
)
```

