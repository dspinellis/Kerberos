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

from .port import Port
from .rest import app
from .state import State, event_processor


def run_rest_server():
    app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    """Program entry point"""
    syslog.openlog(ident="alarm")


    parser = argparse.ArgumentParser(
        description='Alarm daemon')

    parser.add_argument('-d', '--debug',
                        help='Run in debug mode',
                        action='store_true')

    parser.add_argument('file',
                        help='Alarm specification',
                        type=str)
    args = parser.parse_args()
    if args.debug:
        print("Debug option set\n")

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_rest_server, daemon=True)
    flask_thread.start()

    try:
        # Use BCM numbers for ports
        GPIO.setmode(GPIO.BCM)
        with open(args.file, "r") as input_file:
            initial_state_name = read_spec(input_file)

        event_processor(initial_state_name)

    finally:
        GPIO.cleanup()  # Reset GPIO states


if __name__ == "__main__":
    main()
