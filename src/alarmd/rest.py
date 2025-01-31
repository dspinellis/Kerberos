"""Implement alarm's REST interface."""

import syslog

from flask import Flask, abort, jsonify, request

from alarmd.debug import Debug
from alarmd.port import Port
from alarmd.event_queue import event_queue
from alarmd.state import State

# Flask setup
app = Flask(__name__)


def access_check():
    """Only allow localhost requests."""
    if request.remote_addr != "127.0.0.1":
        abort(403)  # Forbidden


@app.route("/cmd/<name>", methods=["GET"])
def rest_cmd(name):
    """
    Function registered to be called when a REST request
    /cmd/<command> is issued.
    This handles commands registered as event transitions for
    all states (*).

    Args:
        name (str): The command's name.

    Returns:
        str: <event name>: "OK"
    """
    access_check()
    event = f"Cmd{name}"
    Debug.log(f"Queuing REST command event {event}")
    if not State.all_states.has_event_transition(event):
        abort(404)  # Not found
    syslog.syslog(syslog.LOG_INFO, f"command: {event}")
    event_queue.put(event)
    return jsonify({event: "OK"})


@app.route("/state", methods=["GET"])
def rest_status():
    """Return the alarm's state."""
    access_check()
    return jsonify(
        {
            "state": State.get_state().get_name(),
        }
    )


@app.route("/sensor/<name>", methods=["GET"])
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
    sensor_port = Port.get_instance_by_name(name)
    if not sensor_port or not sensor_port.is_sensor():
        abort(404)  # Not found
    return jsonify({"value": sensor_port.get_value()})
