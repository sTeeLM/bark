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
    subparsers.required = True  # Enforce the user to choose either 'send' or 'delete'

    # ==================== SUBCOMMAND: SEND ====================
    send_parser = subparsers.add_parser("send", help="Send or update a full-featured notification")

    # 🌟 Required positional argument: If missing, argparse throws error and exits immediately
    send_parser.add_argument("body", type=str, help="Notification message body")

    # Optional arguments for 'send'
    send_parser.add_argument("-k", "--key", type=str, default=None, help="Override Bark Device Key")
    send_parser.add_argument("--server", type=str, default=None, help="Override Bark server URL")
    send_parser.add_argument("-t", "--title", type=str, default=None, help="Notification title")
    send_parser.add_argument("-g", "--group", type=str, default=None, help="Notification group name")
    send_parser.add_argument("-s", "--sound", type=str, default=None, help="Notification sound filename")
    send_parser.add_argument("-l", "--level", type=str, default=None,
                             choices=["active", "time_sensitive", "critical", "passive"],
                             help="Notification interruption level")
    send_parser.add_argument("--icon", type=str, default=None, help="Custom notification icon URL")
    send_parser.add_argument("--url", type=str, default=None, help="Action URL to open when clicked")
    send_parser.add_argument("--badge", type=int, default=None, help="Application badge number")
    send_parser.add_argument("--volume", type=float, default=None, help="Sound volume level (0 to 10)")
    send_parser.add_argument("--ttl", type=int, default=None, help="Time to live in seconds before expiration")
    send_parser.add_argument("--id", type=str, default=None, help="Unique message identifier for future updates/deletions")
    send_parser.add_argument("--call", action="store_true", help="Enable continuous ringtone call alert")
    send_parser.add_argument("--is-archive", type=int, choices=[0, 1], default=None,
                             help="Force archive toggle (1 to save, 0 to skip)")

    # ==================== SUBCOMMAND: DELETE ====================
    delete_parser = subparsers.add_parser("delete", help="Recall/Delete an existing notification from iOS device")

    # Required positional argument for 'delete'
    delete_parser.add_argument("id", type=str, help="The unique message ID to be recalled")

    # Optional arguments for 'delete'
    delete_parser.add_argument("-k", "--key", type=str, default=None, help="Override Bark Device Key")
    delete_parser.add_argument("--server", type=str, default=None, help="Override Bark server URL")

    # 3. Parse inputs (Natively blocks when required arguments are omitted)
    args = parser.parse_args()

    # 4. Instantiate core library with parameter context
    try:
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
            msg_id=args.id
        )

    elif args.command == "delete":
        success, message = notifier.delete(msg_id=args.id)

    # 6. Print uniform exit output
    if success:
        print(message)
    else:
        print(message, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

