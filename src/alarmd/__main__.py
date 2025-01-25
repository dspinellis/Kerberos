#!/usr/bin/env python3
#
# Copyright 2000-2025 Diomidis Spinellis
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Home security alarm daemon
"""

import argparse
import sys
import syslog
import argparse
import threading
import RPi.GPIO as GPIO


from . import debug
from .dsl import read_config
from .port import Port, list_ports, set_emulated
from .rest import app
from .state import State, event_processor


def run_rest_server():
    """Thread callback to run the REST server"""
    app.run(host='127.0.0.1', port=5000, debug=debug.enabled(),
            use_reloader=False)

def main():
    """Program entry point"""
    syslog.openlog(ident="alarm")

    parser = argparse.ArgumentParser(description='Security alarm daemon')

    parser.add_argument('-d', '--debug',
                        help='Run in debug mode',
                        action='store_true')

    parser.add_argument('-e', '--emulate',
                        help='Emulate GPIO',
                        action='store_true')

    parser.add_argument('file',
                        help='Alarm specification',
                        type=str)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--list", action="store_true",
                       help="List available ports")
    group.add_argument("-r", "--reset", metavar="NAME",
                       help="Reset the specified actuator")
    group.add_argument("-s", "--set", metavar="NAME",
                       help="Set the specified actuator")
    group.add_argument("-v", "--values", action="store_true",
                       help="Show sensor values")

    args = parser.parse_args()
    if args.debug:
        debug.enable()

    if args.emulate:
        set_emulated(True)

    try:
        if not args.emulate:
            # Use BCM numbers for ports
            GPIO.setmode(GPIO.BCM)

        # Read description file to setup I/O hardware
        with open(args.file, "r") as input_file:
            initial_state_name = read_config(input_file)

        if args.values:
            sensor_display()
            # Not reached
        if args.set:
            set_value(args.set, 1)
            sys.exit(0)
        if args.reset:
            set_value(args.set, 0)
            sys.exit(0)
        if args.list:
            list_ports()
            sys.exit(0)

        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=run_rest_server, daemon=True)
        flask_thread.start()

        event_processor(initial_state_name)

    finally:
        if not args.emulate:
            GPIO.cleanup()  # Reset GPIO states


if __name__ == "__main__":
    main()
