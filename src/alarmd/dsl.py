import re
import sys

from .port import SensorPort, ActuatorPort

from .state import State, all_states
from .state import __dict__ as state_dict


def read_config(input_file):
    """Read the alarm configuration file, setting up the hardware and
    the event-processing state transition rules.

    Args:
        input_file (File): Opened file to parse.

    Returns:
        str: The name of the state from which to start.
    """
    file_name = input_file.name if hasattr(input_file, "name") else "-"

    current_line_number = 0
    number_of_errors = 0
    initial_state_name = None

    # Currently parsed state
    state = None
    in_python_block = False

    for line in input_file:
        current_line_number += 1
        line = line.rstrip()  # Strip trailing newline

        # Remove comments
        line = re.sub(r"^#.*", "", line).rstrip()

        # Skip empty lines
        if not line:
            continue

        if re.match(r"^SENSOR", line):
            io_type, pcb, physical, bcm, log, name = line.split()
            port = SensorPort(name, pcb, physical, bcm, log)

        elif re.match(r"^ACTUATOR", line):
            io_type, pcb, physical, bcm, log, name = line.split()
            port = ActuatorPort(name, pcb, physical, bcm, log)

        # Python code blocks
        elif line[:3] == "%{":
            in_python_block = True
            python_block_lines = ""
        elif line[:3] == "%}":
            in_python_block = False
            try:
                exec(python_block_lines, state_dict)
            except Exception as e:
                sys.stderr.write(f"{file_name}({current_line_number}): {e}\n")
                number_of_errors += 1
        elif in_python_block:
            python_block_lines += line + "\n"

        elif match := re.match(r"^(\w+):$", line):
            # "name:": Named state begin
            name = match.group(1)
            state = State(name)

        elif re.match(r"^\*:$", line):
            # "*:": Default state transitions, applicable to all
            state = all_states

        elif match := re.match(r"^\%i (\w+)", line):
            # "%i state": Initial state specification
            initial_state_name = match.group(1)

        elif match := re.match(r"^\s*\|([=><]\d+)?\s+(.*)", line):
            # "| command": State entry action
            count = match.group(1)
            command = match.group(2)
            command = re.sub(
                r"ClearCounter\((\w+)\)",
                r'get_instance("\1").clear_counter()',
                command,
            )
            command = re.sub(
                r"call\s+(\w+)", r'get_instance("\1").enter()', command
            )
            if count:
                count = count.replace("=", "==")
                state.add_entry_action(
                    f"{command} if self.counter {count} else None"
                )
            else:
                state.add_entry_action(command)

        elif match := re.match(r"^\s*([\w.]+)?\s*>\s*(\w+)", line):
            # "event > state": State transition
            event_name = match.group(1)
            new_state_name = match.group(2)
            if event_name and re.match(r"^([\d.]+)s$", event_name):
                # "42s": After N seconds
                timer_value = re.match(r"^([\d.]+)s$", event_name).group(1)
                event_name = f"TIMER_{timer_value}"
                state.add_entry_action(
                    f"register_timer_event({timer_value}, '{event_name}')"
                )
            # Event name may be None, which makes it the non-event
            # transition.
            state.add_event_transition(event_name, new_state_name)

        elif re.search(r"\s*;\s*$", line):
            # ";": End of state spec
            continue

        else:
            sys.stderr.write(
                f"{file_name}({current_line_number}): syntax error [{line}]\n"
            )
            number_of_errors += 1

    if number_of_errors:
        sys.stderr.write(
            f"Encountered {number_of_errors} errors during processing.\n"
        )
        sys.exit(1)
    return initial_state_name
