import queue

# System's event queue
# Each event is a string denoting a REST command or a sensor activity
event_queue = queue.Queue()


def put(event):
    """
    Add the specified event to the system's event queue.

    Args:
        event (str): The event's name

    Returns:
        None
    """
    event_queue.put(event)


def get():
    """
    Return the first pending event from the system's event queue.

    Args: None

    Returns:
        str: The event's name
    """
    return event_queue.get()
