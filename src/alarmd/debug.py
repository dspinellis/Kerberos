import sys

enabled = False

def enable():
    global enabled
    enabled = True


def disable():
    global enabled
    enabled = False


def log(*args):
    """
    Logs a debug message with functionality similar to the print function.

    Args:
        *args: The objects to be logged, separated by `sep`.
    """
    if not enabled:
        return
    message = ' '.join(map(str, args))
    print(message, file=sys.stderr, flush=True)
