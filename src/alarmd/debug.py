"""
Debug logging
"""

import sys


class Debug:
    """
    Controllable debug logging
    """

    logging = False

    @classmethod
    def enable(cls):
        """Enable debug logging"""
        cls.logging = True

    @classmethod
    def enabled(cls):
        """Return true if debug loging is enabled"""
        return cls.logging

    @classmethod
    def disable(cls):
        """Disable debugging"""
        cls.logging = False

    @classmethod
    def log(cls, *args):
        """
        Logs a debug message with functionality similar to the print function.

        Args:
            *args: The objects to be logged, separated by `sep`.
        """
        if not cls.enabled():
            return
        message = " ".join(map(str, args))
        print(message, file=sys.stderr, flush=True)
