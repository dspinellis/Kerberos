"""System's event queue"""

import queue

# Each event is a string denoting a REST command or a sensor activity
# Use the get(), put(), and empty() methods on it
event_queue = queue.Queue()
