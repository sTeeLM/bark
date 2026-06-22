# -*- coding: utf-8 -*-
import sys
import argparse
from .core import BarkNotifier

def main():
    parser = argparse.ArgumentParser(description="Bark system-wide CLI tool.")
    parser.add_argument("body", type=str, nargs="?", help="Notification message body")
    parser.add_argument("-k", "--key", type=str, default=None, help="Override Bark Device Key")
    parser.add_argument("--server", type=str, default=None, help="Override Bark server URL")
    parser.add_argument("-t", "--title", type=str, default=None, help="Override notification title")
    parser.add_argument("-g", "--group", type=str, default=None, help="Override notification group")
    parser.add_argument("-s", "--sound", type=str, default=None, help="Override notification sound")
    parser.add_argument("-l", "--level", type=str, default=None,
                        choices=["active", "time_sensitive", "critical", "passive"],
                        help="Override notification level")

    args = parser.parse_args()

    if not args.body:
        parser.print_help()
        sys.exit(0)

    # Catch the ValueError raised from core validation
    try:
        notifier = BarkNotifier(
            key=args.key, server=args.server, title=args.title,
            group=args.group, sound=args.sound, level=args.level
        )
    except ValueError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

    success, message = notifier.send(body=args.body)
    if success:
        print(message)
    else:
        print(message, file=sys.stderr)
        sys.exit(1)

