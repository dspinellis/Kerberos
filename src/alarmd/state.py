import os
import threading

# API functions
from os import system
from time import sleep
from sys import exit
from syslog import syslog, LOG_INFO, LOG_DEBUG, LOG_WARNING, closelog

from . import debug
from . import event_queue
from .port import (increment_sensors, ports, set_bit, set_sensor_active,
                   zero_sensors)


# All states
states_by_name = dict()

class State:
    def __init__(self, name):
        """Constructor to initialize the instance field."""
        self.name = name
        self.counter = 0
        self.entry_actions = []
        self.event_transitions = {}
        states_by_name[name] = self


    def has_event_transitions(self):
        """Return true if the state has event actions associated with it."""
        for k in self.event_transitions:
            if k:
                return True


    def get_name(self):
        """Return the state's name."""
        return self.name


    def clear_counter(self):
        """Zero the state entries counter."""
        self.counter = 0


    def add_entry_action(self, command):
        """Add the specified command string as an entry action."""
        self.entry_actions.append(command)


    def add_event_transition(self, event_name, state_name):
        """Transition to the specified state given an event."""
        self.event_transitions[event_name] = state_name


    def enter(self):
        """Perform the state's entry actions."""
        self.counter += 1
        for action in self.entry_actions:
            debug.log(f"Evaluate {action}")
            eval(action)


    def process_event(self, event_name):
        """Process the specified event return the new state name."""
        if self != all_states:
            if new_state_name := all_states.process_event(event_name):
                return new_state_name
        return self.event_transitions.get(event_name)


    def __eq__(self, other):
        """Check equality based on the name."""
        if not isinstance(other, State):
            return NotImplemented
        return self.name == other.name


    def __hash__(self):
        """Generate a hash based on the name."""
        return hash(self.name)


    def __str__(self):
        """Pretty-print the instance."""
        return f"State {self.name=} {self.counter=}"


    def __repr__(self):
        """Debug representation of the instance."""
        return str(self)


    def get_entry_action(self, n):
        """
        Return the state's specified entry action.

        Args:
            n (int): The ordinal of the entry action to return.

        Returns:
            str: The specified entry action
        """
        return self.entry_actions[n]


    def get_event_transition(self, event):
        """
        Return the state's specified event transition.

        Args:
            event (str): The event transition to return.

        Returns:
            str: The new state after the specified event
        """
        return self.event_transitions[event]



# Event processing common to all states
all_states = State('*')

def get_instance(name):
    """
    Return the state with the specified name.

    Args:
        name (str): The states's name

    Returns:
        State: The object associated with the named state.
    """
    return states_by_name[name]


# DSL API functions
def register_timer_event(delay, event_name):
    """
    Setup a thread to deliver an event named TIMER_N after the specified
    N second delay.

    Args:
        delay (int): The number of seconds to delay
        event_name (str): The event's name

    Returns:
        None
    """
    def enqueue_event_after(delay, event_name):
        sleep(delay)
        event_queue.put(event_name)


    thread = threading.Thread(target=enqueue_event_after,
                              args=(delay, event_name), daemon=True)
    thread.start()


def unlink(file_path):
    """
    Delete the file specified by file_path.

    Args:
        file_path (str): The path specifying the file to delete.

    Returns:
        None
    """
    os.remove(file_path)


def touch(file_path):
    """
    Create the empty file specified by file_path.

    Args:
        file_path (str): The path specifying the file to create.

    Returns:
        None
    """
    with open(file_path, "w") as file:
        pass


def event_processor(initial_state_name):
    """
    Process events from the queue through the configured state machine,
    starting from the specified initial state.

    Args:
        initial_state_name (str): The state from which to start processing.

    Returns:
        None
    """
    state = get_instance(initial_state_name)
    state.enter()

    debug.log("Starting event processing loop...")
    while state.get_name() != 'DONE':
        debug.log(f"{state=}")
        if state.has_event_transitions():
            # Block until an event is available
            event = event_queue.get()
        else:
            event = None
        debug.log(f"Process event {event}")
        new_state_name = state.process_event(event)
        new_state = get_instance(new_state_name)
        debug.log(f"Enter {new_state}")
        if new_state != state:
            state = new_state
            state.enter()
