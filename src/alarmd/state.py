"""State transition engine for handling the DSL-specified configuration."""

import os
import threading
from time import sleep


from alarmd.debug import Debug
from .event_queue import event_queue


class State:
    """State transition engine."""

    # Map from state name to state instance
    states_by_name = {}

    # The current state
    state = None

    # Event processing common to all states
    all_states = None

    @classmethod
    def get_state(cls):
        """
        Return the current state machine state

        Args:
            None

        Returns:
            State: The current state machine state
        """
        return cls.state

    @classmethod
    def reset(cls):
        """Initialize global state variables."""
        cls.state = None
        cls.states_by_name = {}
        cls.all_states = State("*")

    @classmethod
    def event_processor(cls, initial_state_name):
        """
        Process events from the queue through the configured state machine,
        starting from the specified initial state.

        Args:
            initial_state_name (str): The state from which to start processing.

        Returns:
            None
        """
        cls.state = cls.get_instance_by_name(initial_state_name)
        cls.state.enter()

        Debug.log("Starting event processing loop...")
        while cls.state.get_name() != "DONE":
            Debug.log(f"{cls.state=}")
            Debug.log(f"{cls.all_states=}")
            if not cls.state.has_direct_transition():
                # Block until an event is available
                event = event_queue.get()
            else:
                # Execute entry actions and default transition
                event = None
            Debug.log(f"Process event {event}")
            new_state_name = cls.state.process_event(event)
            Debug.log(f"{new_state_name=}")
            new_state = cls.get_instance_by_name(new_state_name)
            Debug.log(f"Enter {new_state}")
            if new_state != cls.state:
                cls.state = new_state
                cls.state.enter()

    @classmethod
    def get_instance_by_name(cls, name):
        """
        Return the state with the specified name.

        Args:
            name (str): The states's name

        Returns:
            State: The object associated with the named state.
        """
        return cls.states_by_name[name]

    def __init__(self, name):
        """Constructor to initialize the instance field."""
        self.name = name
        self.counter = 0
        self.entry_actions = []
        self.event_transitions = {}
        State.states_by_name[name] = self

    def has_direct_transition(self):
        """Return true if the state has a direct (non-event)
        transition associated with it."""
        for k in self.event_transitions:
            if not k:
                return True
        return False

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
            Debug.log(f"Evaluate {action}")
            # pylint: disable-next=eval-used
            eval(action)

    def has_event_transition(self, event_name):
        """Return true if the state directly (not via all_states)
        supports a given event."""
        return bool(self.event_transitions.get(event_name))

    def process_event(self, event_name):
        """Transition on the specified event; return the new state name."""
        if self != State.all_states:
            if new_state_name := State.all_states.process_event(event_name):
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
        return f"State {self.name=} {self.counter=} {self.event_transitions=}"

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


State.all_states = State("*")


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

    thread = threading.Thread(
        target=enqueue_event_after, args=(delay, event_name), daemon=True
    )
    thread.start()


def unlink(file_path):
    """
    Delete the file specified by file_path without failure if the file
    does not exist.

    Args:
        file_path (str): The path specifying the file to delete.

    Returns:
        None
    """
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass


def touch(file_path):
    """
    Create the empty file specified by file_path.

    Args:
        file_path (str): The path specifying the file to create.

    Returns:
        None
    """
    with open(file_path, "wb"):
        pass
