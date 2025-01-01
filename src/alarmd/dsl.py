import importlib
import re
import RPi.GPIO as GPIO
import sys

from .port import Port

from .state import State, all_states
from . import state
from . import state as import_target


def dynamic_import(source_module_name, component_names, target_module):
    """
    Dynamically imports specific elements from the specified
    source module and injects them into the globals of a specified
    target module.

    Args:
        source_module_name (str): The module containing the elements
        component_names (str): Comma-separated names of components to import
        target_module (module): The module where the imports
        should be injected.

    Raises:
        ImportError: If any specified element cannot be imported or if
        the source or target module does not exist.
    """
    components = [comp.strip() for comp in component_names.split(",")]
    source_module = importlib.import_module(source_module_name)

    # Inject components into the target module's globals
    target_globals = target_module.__dict__
    for component in components:
        if not hasattr(source_module, component):
            raise ImportError(f"Cannot import name '{component}' from '{source_module_name}'")
        target_globals[component] = getattr(source_module, component)


def read_config(input_file):
    """Read the alarm configuration file, setting up the hardware and
    the event-processing state transition rules.

    Args:
        input_file (File): Opened file to parse.

    Returns:
        str: The name of the state from which to start.
    """
    current_line_number = 0
    number_of_errors = 0
    initial_state_name = None

    # Currently parsed state
    state = None

    for line in input_file:
        current_line_number += 1
        line = line.rstrip()  # Strip trailing newline

        # Remove comments
        line = re.sub(r'^#.*', '', line).strip()

        # Skip empty lines
        if not line:
            continue

        if re.match(r'^(SENSOR|RELAY)', line):
            io_type, pcb, physical, bcm, log, name = line.split()
            port = Port(name, io_type, pcb, physical, bcm, log)

        elif match := re.match(r"from\s+(\S+)\s+import\s+(.+)", line):
            # "from name import c1, c2": Import components to use
            dynamic_import(match.group(1).strip(), match.group(2),
                           import_target)
        elif match := re.match(r'^(\w+):$', line):
            # "name:": Named state begin
            name = match.group(1)
            state = State(name)

        elif re.match(r'^\*:$', line):
            # "*:": Default state transitions, applicable to all
            state = all_states

        elif match := re.match(r'^\%i (\w+)', line):
            # "%i state": Initial state specification
            initial_state_name = match.group(1)

        elif match := re.match(r'^\s*\|([=><]\d+)?\s+(.*)', line):
            # "| command": State entry action
            count = match.group(1)
            command = match.group(2)
            command = re.sub(r'ClearCounter\((\w+)\)', r'get_instance("\1").clear_counter()', command)
            command = re.sub(r'call\s+(\w+)', r'get_instance("\1").enter()', command)
            if count:
                count = count.replace("=", "==")
                state.add_entry_action(f"{command} if self.counter {count} else None")
            else:
                state.add_entry_action(command)

        elif match := re.match(r'^\s*([\w.]+)?\s*>\s*(\w+)', line):
            # "event > state": State transition
            event_name = match.group(1)
            new_state_name = match.group(2)
            if event_name and re.match(r'^([\d.]+)s$', event_name):
                # "42s": After N seconds
                timer_value = re.match(r'^([\d.]+)s$', event_name).group(1)
                event_name = f"TIMER_{timer_value}"
                state.add_entry_action(f"register_timer_event({timer_value}, '{event_name}')")
            # Event name may be None, which makes it the non-event
            # transition.
            state.add_event_transition(event_name, new_state_name)

        elif re.search(r'\s*;\s*$', line):
            # ";": End of state spec
            continue

        else:
            name = input_file.name if hasattr(input_file, 'name') else '-';
            sys.stderr.write(f"{name}({current_line_number}): syntax error [{line}]\n")
            number_of_errors += 1

    if number_of_errors:
        sys.stderr.write(f"Encountered {number_of_errors} errors during processing.\n")
        sys.exit(1)
    return initial_state_name
