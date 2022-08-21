"""
Perform an action on the aurweb config.

When AUR_CONFIG_IMMUTABLE is set, the `set` action is noop.
"""
import argparse
import configparser
import os
import sys

import aurweb.config


def do_action(func, *args, save: bool = True):
    # If AUR_CONFIG_IMMUTABLE is defined, skip out on config setting.
    if int(os.environ.get("AUR_CONFIG_IMMUTABLE", 0)):
        return

    value = None
    try:
        value = func(*args)
        if save:
            aurweb.config.save()
    except configparser.NoSectionError:
        print("error: no section found", file=sys.stderr)
    except configparser.NoOptionError:
        print("error: no option found", file=sys.stderr)

    return value


def action_set(args):
    if not args.value:
        print("error: no value provided", file=sys.stderr)
        return
    do_action(aurweb.config.set_option, args.section, args.option, args.value)


def action_unset(args):
    do_action(aurweb.config.unset_option, args.section, args.option)


def action_get(args):
    val = do_action(aurweb.config.get, args.section, args.option, save=False)
    print(val)


def parse_args():
    fmt_cls = argparse.RawDescriptionHelpFormatter
    actions = ["get", "set", "unset"]
    parser = argparse.ArgumentParser(
        description="aurweb configuration tool",
        formatter_class=lambda prog: fmt_cls(prog=prog, max_help_position=80),
    )
    parser.add_argument("action", choices=actions, help="script action")
    parser.add_argument("section", help="config section")
    parser.add_argument("option", help="config option")
    parser.add_argument("value", nargs="?", default=0, help="config option value")
    return parser.parse_args()


def main():
    args = parse_args()
    action = getattr(sys.modules[__name__], f"action_{args.action}")
    return action(args)


if __name__ == "__main__":
    main()
