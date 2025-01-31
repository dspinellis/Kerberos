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
CLI command class
"""

import re


class Command:
    """A record encapsulating a CLI command's attributes."""

    def __init__(self, letter, event_name, description):
        self.letter = letter
        self.event_name = event_name
        self.description = description

    def get_letter(self):
        """Return the command's single letter mnemonic."""
        return self.letter

    def get_event_name(self):
        """Return the command's name."""
        return self.event_name

    def get_description(self):
        """Return the command's longer description."""
        return self.description

    def get_cli_name(self):
        """
        Return the command's event name converted from a camel case string
        to kebab case, e.g. for CLI options.

        Returns:
            str: The eventName converted event-name
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "-", self.event_name).lower()

    def get_option_name(self):
        """
        Returns the event name converted from a camel case string
        to snake case, e.g. for getting argparse options.

        Returns:
            str: The eventName converted event_name
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "_", self.event_name).lower()
