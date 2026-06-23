# -*- coding: utf-8 -*-
import sys
import argparse
from .core import BarkNotifier

def main():
    # 1. Base argument parser
    parser = argparse.ArgumentParser(
        description="Bark system-wide CLI tool with strict subcommand syntax.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # 2. Add subparsers for 'send' and 'delete'
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    subparsers.required = True

    # ==================== SUBCOMMAND: SEND ====================
    send_parser = subparsers.add_parser("send", help="Send or update a full-featured notification")

    # Required positional argument for the message body
    send_parser.add_argument("body", type=str, help="Notification message body")

    # Core config overrides
    send_parser.add_argument("-k", "--key", type=str, default=None, help="Override Bark Device Key")
    send_parser.add_argument("--server", type=str, default=None, help="Override Bark server URL")
    send_parser.add_argument("-v", "--verbose", action="store_true", help="Print outbound and inbound network payloads")

    # Added Timestamp Override Option via CLI
    send_parser.add_argument("--timestamp", type=str, default=None, choices=["true", "false"], help="Override timestamp prefix toggle")

    # Advanced encryption overrides via CLI
    send_parser.add_argument("--encryption", type=str, default=None, choices=["true", "false"], help="Override encryption toggle")
    send_parser.add_argument("--enc-key", type=str, default=None, help="Override encryption key string")
    send_parser.add_argument("--enc-iv", type=str, default=None, help="Override initialization vector")
    send_parser.add_argument("--enc-algo", type=str, default=None, choices=["aes128", "aes192", "aes256"], help="Override encryption algorithm")
    send_parser.add_argument("--enc-mode", type=str, default=None, choices=["cbc", "ecb", "gcm"], help="Override encryption mechanism")

    # Advanced official Bark V2 notification parameters
    send_parser.add_argument("-t", "--title", type=str, default=None, help="Notification title")
    send_parser.add_argument("-g", "--group", type=str, default=None, help="Notification group name")
    send_parser.add_argument("-s", "--sound", type=str, default=None, help="Notification sound filename")
    send_parser.add_argument("-l", "--level", type=str, default=None,
                             choices=["active", "time_sensitive", "critical", "passive"],
                             help="Notification level")
    send_parser.add_argument("--icon", type=str, default=None, help="Custom notification icon URL")
    send_parser.add_argument("--url", type=str, default=None, help="Action URL to open when clicked")
    send_parser.add_argument("--badge", type=int, default=None, help="Application badge number")
    send_parser.add_argument("--volume", type=float, default=None, help="Sound volume level (0 to 10)")
    send_parser.add_argument("--ttl", type=int, default=None, help="Time to live in seconds before expiration")
    send_parser.add_argument("--id", type=str, default=None, help="Unique message identifier")
    send_parser.add_argument("--call", action="store_true", help="Enable continuous ringtone call alert")

    # Fixed: Added exact constraint bounds [0, 1] to prevent SyntaxError compiler crashes
    send_parser.add_argument("--is-archive", type=int, choices=[0, 1], default=None, help="Force archive toggle")

    # ==================== SUBCOMMAND: DELETE ====================
    delete_parser = subparsers.add_parser("delete", help="Recall/Delete an existing notification from iOS device")

    # Required positional argument for 'delete'
    delete_parser.add_argument("id", type=str, help="The unique message ID to be recalled")

    # Core config overrides
    delete_parser.add_argument("-k", "--key", type=str, default=None, help="Override Bark Device Key")
    delete_parser.add_argument("--server", type=str, default=None, help="Override Bark server URL")
    delete_parser.add_argument("-v", "--verbose", action="store_true", help="Print outbound and inbound network payloads")

    # 3. Parse inputs according to strict subcommand positioning
    args = parser.parse_args()

    # 4. Instantiate core library with full parameter context
    try:
        if args.command == "send":
            notifier = BarkNotifier(
                key=args.key,
                server=args.server,
                timestamp=args.timestamp,
                encryption=args.encryption,
                enc_key=args.enc_key,
                enc_iv=args.enc_iv,
                enc_algo=args.enc_algo,
                enc_mode=args.enc_mode
            )
        else:
            notifier = BarkNotifier(key=args.key, server=args.server)
    except ValueError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

    # 5. Process execution based on exact subcommand chosen
    if args.command == "send":
        cli_level = args.level
        mapped_level = "time_sensitive" if cli_level == "time_sensitive" else cli_level

        success, message = notifier.send(
            body=args.body,
            title=args.title,
            group=args.group,
            sound=args.sound,
            level=mapped_level,
            icon=args.icon,
            url=args.url,
            is_archive=args.is_archive,
            badge=args.badge,
            volume=args.volume,
            call=args.call,
            ttl=args.ttl,
            msg_id=args.id,
            verbose=args.verbose,
            timestamp=args.timestamp
        )

    elif args.command == "delete":
        success, message = notifier.delete(
            msg_id=args.id,
            verbose=args.verbose
        )

    # 6. Print uniform exit output
    if success:
        print(message)
    else:
        print(message, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

