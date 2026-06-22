# -*- coding: utf-8 -*-
import os
import json
import configparser
import urllib.request
import urllib.error

class BarkNotifier:
    def __init__(self, key=None, server=None, title=None, group=None, sound=None, level=None, icon=None):
        config_path = "/etc/bark/bark.conf"
        config = configparser.ConfigParser()
        conf_data = {}

        if os.path.exists(config_path):
            try:
                config.read(config_path, encoding='utf-8')
                if 'DEFAULT' in config:
                    conf_data = config['DEFAULT']
            except Exception:
                pass

        raw_key = key or conf_data.get("key", "")
        self.key = raw_key.strip() if raw_key else ""

        if not self.key:
            raise ValueError(
                f"Error: Bark Device Key is empty. "
                f"Please ensure the config file exists and contains a valid key at: {config_path}"
            )

        self.server = server or conf_data.get("server", "https://day.app")
        self.title = title or conf_data.get("title", "Server Notification")
        self.group = group or conf_data.get("group", "Default")
        self.sound = sound or conf_data.get("sound", "chimes")
        self.icon = icon or conf_data.get("icon", "")

        raw_level = level or conf_data.get("level", "active")
        self.level = "timeSensitive" if raw_level == "time_sensitive" else raw_level

    def send(self, body, title=None, group=None, msg_id=None, sound=None, level=None, icon=None,
             url=None, is_archive=None, badge=None, volume=None, call=False, ttl=None,
             ciphertext=None, iv=None):
        """
        Send a full-featured Bark notification.
        Supports all arguments defined in the official Bark documentation.
        """
        raw_level = level or self.level
        final_level = "timeSensitive" if raw_level == "time_sensitive" else raw_level

        # 1. Base required payload properties
        payload = {
            "device_key": self.key,
            "title": title or self.title,
            "body": str(body),
            "group": group or self.group,
            "sound": sound or self.sound,
            "level": final_level
        }

        # 2. Custom Icon URL
        final_icon = icon or self.icon
        if final_icon:
            payload["icon"] = final_icon

        # 3. Action URL (Click destination)
        if url:
            payload["url"] = url

        # 4. Archive Toggle (1 = force save, 0 = do not save)
        if is_archive is not None:
            payload["isArchive"] = 1 if is_archive else 0

        # 5. Badge Count (Application icon badge number)
        if badge is not None:
            try:
                payload["badge"] = int(badge)
            except (ValueError, TypeError):
                pass

        # 6. Sound Volume (Float or Int from 0 to 10)
        if volume is not None:
            try:
                payload["volume"] = float(volume)
            except (ValueError, TypeError):
                pass

        # 7. Continuous Ringtone Alert
        if call:
            payload["call"] = 1

        # 8. Time To Live (Auto-deletion expiration in seconds)
        if ttl is not None:
            try:
                payload["ttl"] = int(ttl)
            except (ValueError, TypeError):
                pass

        # 9. Payload Encryption Properties (AES-128-CBC / AES-256-CBC)
        if ciphertext:
            payload["ciphertext"] = str(ciphertext)
        if iv:
            payload["iv"] = str(iv)

        # 10. ID
        if msg_id:
            payload["id"] = str(msg_id)


        # 11. Process network transmission
        target_url = f"{self.server.rstrip('/')}/push"
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            target_url, data=req_data,
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

    def delete(self, msg_id):
        """
        核心删除/撤回接口
        必须包含 device_key, id, 并设置 delete="1"
        """
        if not msg_id: return False, "msg_id required"
        payload = {
            "device_key": self.key,
            "id": str(msg_id),
            "delete": "1"
        }
        return self._execute_request(payload)
