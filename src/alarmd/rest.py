from flask import Flask, jsonify

from . import debug, event_queue

# Flask setup
app = Flask(__name__)

def rest_cmd(name):
    """
    Function registered to be called when a REST request
    /cmd/<command> is issued.

    Args:
        namr (str): The command's name.

    Returns:
        str: eventname: "OK"
    """
    event = f"Cmd{name}"
    debug.log(f"Queuing REST command event {event}")
    event_queue.put(event)
    return jsonify({event: "OK"})
