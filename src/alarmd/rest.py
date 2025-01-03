from flask import Flask, abort, jsonify

from . import debug
from .event_queue import event_queue
from .state import get_state, all_states

# Flask setup
app = Flask(__name__)

@app.route('/cmd/<name>', methods=['GET'])
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
    if not all_states.has_event_transition(event):
        abort(404)
    event_queue.put(event)
    return jsonify({event: "OK"})


@app.route('/state')
def rest_status():
    return jsonify({
        "state": get_state().get_name(),
    })
