# -*- coding: utf-8 -*-
import os
import json
import configparser
import urllib.request
import urllib.error
import subprocess

class BarkNotifier:
    def __init__(self, key=None, server=None, title=None, group=None, sound=None, level=None,
                 encryption=None, enc_key=None, enc_iv=None, enc_algo=None, enc_mode=None):
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

        raw_level = level or conf_data.get("level", "active")
        self.level = "timeSensitive" if raw_level == "time_sensitive" else raw_level

        raw_enc = encryption or conf_data.get("encryption", "false")
        self.encryption = str(raw_enc).strip().lower() in ("true", "1", "yes", "on")

        self.enc_key = enc_key or conf_data.get("encryption_key", "")
        self.enc_iv = enc_iv or conf_data.get("iv", "")
        self.enc_algo = (enc_algo or conf_data.get("encryption_algorithm", "aes256")).strip().lower()
        self.enc_mode = (enc_mode or conf_data.get("encryption_mechanism", "cbc")).strip().lower()

        if self.encryption:
            algo_key_lengths = {
                "aes128": 16,
                "aes192": 24,
                "aes256": 32
            }

            if self.enc_algo not in algo_key_lengths:
                raise ValueError(f"Error: Unsupported encryption_algorithm '{self.enc_algo}'. Must be aes128, aes192, or aes256.")

            expected_key_len = algo_key_lengths[self.enc_algo]
            actual_key_len = len(self.enc_key.encode('utf-8'))

            if actual_key_len != expected_key_len:
                raise ValueError(f"Error: Encryption key for '{self.enc_algo}' must be exactly {expected_key_len} bytes long. Current length: {actual_key_len} bytes.")

            if self.enc_mode != "ecb":
                expected_iv_len = 16
                actual_iv_len = len(self.enc_iv.encode('utf-8'))
                if actual_iv_len != expected_iv_len:
                    raise ValueError(f"Error: IV for '{self.enc_mode}' mode must be exactly {expected_iv_len} bytes long. Current length: {actual_iv_len} bytes.")

    def _encrypt_payload(self, plaintext_json):
        algo_mapping = {"aes128": "aes-128", "aes192": "aes-192", "aes256": "aes-256"}
        base_algo = algo_mapping.get(self.enc_algo, "aes-256")
        openssl_cipher = f"-{base_algo}-{self.enc_mode}"

        has_iv = self.enc_mode != "ecb"
        hex_key = self.enc_key.encode('utf-8').hex()
        hex_iv = self.enc_iv.encode('utf-8').hex() if has_iv else ""

        cmd = ["openssl", "enc", openssl_cipher, "-K", hex_key]
        if has_iv and hex_iv:
            cmd.extend(["-iv", hex_iv])
        cmd.extend(["-base64", "-A"])

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = proc.communicate(input=plaintext_json.encode('utf-8'))

            if proc.returncode != 0:
                raise RuntimeError(f"OpenSSL internal crash: {stderr_bytes.decode('utf-8').strip()}")

            return stdout_bytes.decode('utf-8').strip()
        except Exception as err:
            raise RuntimeError(f"Failed to execute cryptography subsystem: {err}")

    def send(self, body, title=None, group=None, sound=None, level=None, icon=None,
             url=None, is_archive=None, badge=None, volume=None, call=False, ttl=None, msg_id=None,
             verbose=False):

        raw_level = level or self.level
        final_level = "timeSensitive" if raw_level == "time_sensitive" else raw_level

        inner_payload = {
            "title": title or self.title,
            "body": str(body),
            "group": group or self.group,
            "sound": sound or self.sound,
            "level": final_level
        }

        if icon: inner_payload["icon"] = icon
        if url: inner_payload["url"] = url
        if msg_id: inner_payload["id"] = str(msg_id)
        if is_archive is not None: inner_payload["isArchive"] = 1 if is_archive else 0
        if badge is not None: inner_payload["badge"] = int(badge)
        if volume is not None: inner_payload["volume"] = float(volume)
        if call: inner_payload["call"] = 1
        if ttl is not None: inner_payload["ttl"] = int(ttl)

        json_string = json.dumps(inner_payload, separators=(',', ':'))

        if self.encryption:
            try:
                ciphertext = self._encrypt_payload(json_string)
                outer_payload = {
                    "device_key": self.key,
                    "ciphertext": ciphertext
                }
                if self.enc_iv and self.enc_mode != "ecb":
                    outer_payload["iv"] = self.enc_iv
            except Exception as enc_err:
                return False, f"Encryption subsystem fault: {enc_err}"
        else:
            outer_payload = inner_payload
            outer_payload["device_key"] = self.key

        if verbose:
            print("--- Outbound Payload ---")
            print(json.dumps(outer_payload, indent=2))

        target_url = f"{self.server.rstrip('/')}/push"
        req_data = json.dumps(outer_payload).encode('utf-8')
        req = urllib.request.Request(
            target_url, data=req_data,
            headers={'Content-Type': 'application/json; charset=utf-8'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')

                if verbose:
                    print("--- Inbound Response ---")
                    print(f"HTTP Status: {response.status}")
                    try:
                        print(json.dumps(json.loads(res_body), indent=2))
                    except ValueError:
                        print(res_body)

                res_json = json.loads(res_body)
                if response.status == 200 and res_json.get("code") == 200:
                    return True, "Notification sent successfully"
                return False, f"Server rejected: {res_body}"
        except urllib.error.HTTPError as e:
            res_body = e.read().decode('utf-8')
            if verbose:
                print("--- Inbound Response ---")
                print(f"HTTP Status: {e.code}")
                try:
                    print(json.dumps(json.loads(res_body), indent=2))
                except ValueError:
                    print(res_body)
            return False, f"Network HTTP Error {e.code}: {res_body}"
        except urllib.error.URLError as e:
            return False, f"Network request failed: {e}"

    def delete(self, msg_id, verbose=False):
        if not msg_id:
            return False, "Error: msg_id is required for deletion operation"
        payload = {
            "device_key": self.key,
            "id": str(msg_id),
            "delete": "1"
        }

        if verbose:
            print("--- Outbound Payload ---")
            print(json.dumps(payload, indent=2))

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

                if verbose:
                    print("--- Inbound Response ---")
                    print(f"HTTP Status: {response.status}")
                    try:
                        print(json.dumps(json.loads(res_body), indent=2))
                    except ValueError:
                        print(res_body)

                res_json = json.loads(res_body)
                if response.status == 200 and res_json.get("code") == 200:
                    return True, "Deletion message sent successfully"
                return False, f"Server rejected: {res_body}"
        except urllib.error.HTTPError as e:
            res_body = e.read().decode('utf-8')
            if verbose:
                print("--- Inbound Response ---")
                print(f"HTTP Status: {e.code}")
                try:
                    print(json.dumps(json.loads(res_body), indent=2))
                except ValueError:
                    print(res_body)
            return False, f"Network HTTP Error {e.code}: {res_body}"
        except urllib.error.URLError as e:
            return False, f"Network request failed: {e}"

