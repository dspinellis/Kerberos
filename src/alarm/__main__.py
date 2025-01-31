#!/usr/bin/env python3
#
# Kerberos interface program
#
# Kerberos DSL-configurable alarm program
# Copyright (C) 2000-2025  Diomidis Spinellis - dds@aueb.gr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Home security alarm CLI
"""

import argparse
import sys

import requests

from alarm.commands import commands

ALARM_PORT = 5000

commands_by_letter = {c.get_letter(): c for c in commands}


def run_command(command):
    """
    Issue an HTTP request to the alarm daemon for the specified command

    Args:
        command (Command): The command for which to issue the request.

    Returns:
        str: The HTTP result

    Raises:
        RequestException: If the request fails.
    """

    url = f"http://localhost:{ALARM_PORT}/cmd/{command}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.text


def shell_help():
    """Display available commands."""
    print("Valid commands are:")
    print("x: eXit this command line interface")

    for cmd in commands:
        print(f"{cmd.get_letter()}: {cmd.get_description()}")


def shell():
    """Prompt for commands and execute them."""
    shell_help()

    while True:
        letter = input("Enter remote command: ")[0]

        if letter == "x":
            sys.exit(0)

        command = commands_by_letter.get(letter)

        if not command:
            shell_help()
            continue

        try:
            run_command(command)
        except requests.exceptions.RequestException as exc:
            print(f"Request error: {exc}")


def main():
    """Program entry point"""

    parser = argparse.ArgumentParser(description="Security alarm CLI")

    group = parser.add_mutually_exclusive_group()

    for cmd in commands:
        group.add_argument(
            f"-{cmd.get_letter()}",
            f"--{cmd.get_cli_name()}",
            action="store_true",
            help=cmd.get_description(),
        )

    args = parser.parse_args()

    # Determine passed option
    option = None
    for cmd in commands:
        if getattr(args, cmd.get_option_name()):
            option = cmd.get_letter()
            break

    if option:
        try:
            run_command(commands_by_letter[option])
            sys.exit(0)
        except requests.exceptions.RequestException as exc:
            print(f"Request error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        shell()


if __name__ == "__main__":
    main()
