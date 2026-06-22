# -*- coding: utf-8 -*-
import os
import json
import configparser
import urllib.request
import urllib.error
from importlib.resources import files

class BarkNotifier:
    def __init__(self, key=None, server=None, title=None, group=None, sound=None, level=None):
        # 1. Safely locate the installed bark.conf within site-packages
        conf_data = {}
        try:
            config_path = files('bark_notifier').joinpath('bark.conf')
            if config_path.is_file():
                config = configparser.ConfigParser()
                # Read via string or file context to ensure cross-platform compatibility
                config.read_string(config_path.read_text(encoding='utf-8'))
                if 'DEFAULT' in config:
                    conf_data = config['DEFAULT']
        except Exception:
            pass

        # 2. Priority: Explicit Argument > Configuration File
        raw_key = key or conf_data.get("key", "")
        self.key = raw_key.strip() if raw_key else ""

        # 3. Enforce validation: Raise ValueError if the final Key is empty
        if not self.key:
            installed_path = str(files('bark_notifier').joinpath('bark.conf'))
            raise ValueError(f"Error: Bark Device Key is empty. Please configure it in: {installed_path}")

        # 4. Initialize other parameters
        self.server = server or conf_data.get("server", "https://day.app")
        self.title = title or conf_data.get("title", "Server Notification")
        self.group = group or conf_data.get("group", "Default")
        self.sound = sound or conf_data.get("sound", "chimes")
        
        raw_level = level or conf_data.get("level", "active")
        self.level = "timeSensitive" if raw_level == "time_sensitive" else raw_level

    def send(self, body, title=None, group=None, sound=None, level=None):
        raw_level = level or self.level
        final_level = "timeSensitive" if raw_level == "time_sensitive" else raw_level

        payload = {
            "device_key": self.key,
            "title": title or self.title,
            "body": str(body),
            "group": group or self.group,
            "sound": sound or self.sound,
            "level": final_level
        }

        url = f"{self.server.rstrip('/')}/push"
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, data=req_data, 
            headers={'Content-Type': 'application/json; charset=utf-8'}, 
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                res_json = json.loads(res_body)
                if response.status == 200 and res_json.get("code") == 200:
                    return True, "Notification sent successfully"
                return False, f"Server rejected: {res_body}"
        except urllib.error.URLError as e:
            return False, f"Network request failed: {e}"

