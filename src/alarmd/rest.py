from flask import Flask, abort, jsonify, request
import RPi.GPIO as GPIO

from . import debug, port
from .event_queue import event_queue
from .state import get_state, all_states

# Flask setup
app = Flask(__name__)

def access_check():
    """Only allow localhost requests."""
    if request.remote_addr != '127.0.0.1':
        abort(403) # Forbidden


@app.route('/cmd/<name>', methods=['GET'])
def rest_cmd(name):
    """
    Function registered to be called when a REST request
    /cmd/<command> is issued.

    Args:
        name (str): The command's name.

    Returns:
        str: <event name>: "OK"
    """
    access_check()
    event = f"Cmd{name}"
    debug.log(f"Queuing REST command event {event}")
    if not all_states.has_event_transition(event):
        abort(404) # Not found
    event_queue.put(event)
    return jsonify({event: "OK"})


@app.route('/state', methods=['GET'])
def rest_status():
    access_check()
    return jsonify({
        "state": get_state().get_name(),
    })


@app.route('/sensor/<name>', methods=['GET'])
def rest_sensor(name):
    """
    Function registered to be called when a REST request
    /sensor/<command> is issued.

    Args:
        sensor (str): The sensor's name.

    Returns:
        str: JSON with the following structure
            "value": <port-value>
    """
    access_check()
    sensor_port = port.get_instance(name)
    if not sensor_port or not sensor_port.is_sensor():
        abort(404) # Not found
    return jsonify({"value": sensor_port.get_value()})
