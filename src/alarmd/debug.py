import sys

debug_enabled = False

def enable():
    """Enable debugging"""
    global debug_enabled
    debug_enabled = True


def enabled():
    """Return true if debugging is enabled"""
    return debug_enabled


def disable():
    """Disable debugging"""
    global debug_enabled
    debug_enabled = False


def log(*args):
    """
    Logs a debug message with functionality similar to the print function.

    Args:
        *args: The objects to be logged, separated by `sep`.
    """
    if not enabled():
        return
    message = ' '.join(map(str, args))
    print(message, file=sys.stderr, flush=True)
