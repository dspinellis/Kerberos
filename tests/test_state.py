import pytest
from io import StringIO
from unittest.mock import patch, call
import sys

from alarmd.dsl import read_config
from alarmd.event_queue import event_queue
from alarmd.state import event_processor
from alarmd import debug, port


SETUP = """
# Required API functions
%{
from os import system
from time import sleep
from sys import exit
from syslog import syslog, LOG_INFO, LOG_DEBUG, LOG_WARNING, closelog
from .port import increment_sensors, zero_sensors
from .port import set_bit, set_sensor_event
from .vmqueue import vmqueue
%}

#Type	        PCB	PhysBCM	Log	Name
ACTUATOR	    A1	29	5	1	Siren5
ACTUATOR	    A2	29	6	0	Siren6

%i initial

DONE:
    ;
"""

SENSOR_SETUP = """
#Type	    PCB	PhysBCM	Log	Name
SENSOR	    S04	28	81	1	Bedroom
SENSOR	    S07	40	82	1	Window
"""

@pytest.fixture(autouse=True)
def reset_globals():
    """Fixture to reset global variables before each test."""
    port.reset_globals()

def test_entry_actions():
    mock_file = StringIO(SETUP + """
initial:
    | set_bit('Siren5', 1)
    | set_bit('Siren6', 0)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    siren6 = port.get_instance("Siren6")
    with patch.object(siren5, "set_value") as mock_siren5_set_value, \
        patch.object(siren6, "set_value") as mock_siren6_set_value:
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])
        mock_siren6_set_value.assert_has_calls([call(0)])

def test_simple_transition():
    mock_file = StringIO(SETUP + """
initial:
    | set_bit('Siren5', 1)
    > second
    ;

second:
    | set_bit('Siren6', 0)
    > DONE

other:
    | set_bit('Siren6', 1)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    siren6 = port.get_instance("Siren6")
    with patch.object(siren5, "set_value") as mock_siren5_set_value, \
        patch.object(siren6, "set_value") as mock_siren6_set_value:
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])
        mock_siren6_set_value.assert_has_calls([call(0)])

def test_event_transition():
    mock_file = StringIO(SETUP + """
initial:
    | set_bit('Siren5', 1)
    go_other > other
    go_second > second
    ;

second:
    | set_bit('Siren6', 0)
    > DONE

other:
    | set_bit('Siren6', 1)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    siren6 = port.get_instance("Siren6")
    with patch.object(siren5, "set_value") as mock_siren5_set_value, \
        patch.object(siren6, "set_value") as mock_siren6_set_value:
        event_queue.put('go_second')
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])
        mock_siren6_set_value.assert_has_calls([call(0)])

def test_counter_eq1_action():
    mock_file = StringIO(SETUP + """
initial:
    |=1 set_bit('Siren5', 1)
    repeat > trampoline
    done > DONE
    ;

trampoline:
    > initial
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    with patch.object(siren5, "set_value") as mock_siren5_set_value:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])

def test_counter_eq2_action():
    mock_file = StringIO(SETUP + """
initial:
    |=2 set_bit('Siren5', 1)
    repeat > trampoline
    done > DONE
    ;

trampoline:
    > initial
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    with patch.object(siren5, "set_value") as mock_siren5_set_value:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])

def test_counter_lt3_action():
    mock_file = StringIO(SETUP + """
initial:
    |<3 set_bit('Siren5', 1)
    repeat > trampoline
    done > DONE
    ;

trampoline:
    > initial
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    with patch.object(siren5, "set_value") as mock_siren5_set_value:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        event_processor(initial_name)
        assert mock_siren5_set_value.call_count == 2


def test_timer_action():
    mock_file = StringIO(SETUP + """
initial:
    | set_bit('Siren5', 1)
    go_other > other
    0.1s > second
    ;

second:
    | set_bit('Siren6', 0)
    > DONE

other:
    | set_bit('Siren6', 1)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    siren6 = port.get_instance("Siren6")
    with patch.object(siren5, "set_value") as mock_siren5_set_value, \
        patch.object(siren6, "set_value") as mock_siren6_set_value:
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])
        mock_siren6_set_value.assert_has_calls([call(0)])


def test_event_over_timer_action():
    mock_file = StringIO(SETUP + """
initial:
    | set_bit('Siren5', 1)
    go_second > second
    100s > other
    ;

second:
    | set_bit('Siren6', 0)
    > DONE

other:
    | set_bit('Siren6', 1)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    siren6 = port.get_instance("Siren6")
    with patch.object(siren5, "set_value") as mock_siren5_set_value, \
        patch.object(siren6, "set_value") as mock_siren6_set_value:
        event_queue.put('go_second')
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])
        mock_siren6_set_value.assert_has_calls([call(0)])


def test_call():
    mock_file = StringIO(SETUP + """
initial:
    | call called
    | set_bit('Siren5', 1)
    > DONE
    ;

called:
    | set_bit('Siren6', 0)
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    siren6 = port.get_instance("Siren6")
    with patch.object(siren5, "set_value") as mock_siren5_set_value, \
        patch.object(siren6, "set_value") as mock_siren6_set_value:
        event_processor(initial_name)
        mock_siren5_set_value.assert_has_calls([call(1)])
        mock_siren6_set_value.assert_has_calls([call(0)])

def test_clearcounter_action():
    mock_file = StringIO(SETUP + """
initial:
    |=1 set_bit('Siren5', 1)
    repeat > trampoline
    done > DONE
    ;

trampoline:
    | ClearCounter(initial)
    > initial
    ;
    """)
    initial_name = read_config(mock_file)
    siren5 = port.get_instance("Siren5")
    with patch.object(siren5, "set_value") as mock_siren5_set_value:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        event_processor(initial_name)
        assert mock_siren5_set_value.call_count == 3


def test_api():
    # Test the existence of the external API functions
    mock_file = StringIO(SETUP + """
initial:
    | callable(exit)
    | callable(syslog)
    | callable(closelog)
    | callable(sleep)
    | callable(system)
    | callable(unlink)
    | callable(touch)
    | callable(vmqueue)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    event_processor(initial_name)

def test_set_sensor_event():
    mock_file = StringIO(SENSOR_SETUP + SETUP + """
initial:
    | set_sensor_event("Bedroom", "ActiveSensor")
    > DONE
    ;

clear:
    | set_sensor_event("Bedroom", None)
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    assert not port.get_instance('Bedroom').is_event_generating()
    event_processor(initial_name)
    assert port.get_instance('Bedroom').is_event_generating()
    event_processor('clear')
    assert not port.get_instance('Bedroom').is_event_generating()


def test_increment_sensors():
    mock_file = StringIO(SENSOR_SETUP + SETUP + """
initial:
    | set_sensor_event("Bedroom", "ActiveSensor")
    | increment_sensors()
    > DONE
    ;

zero:
    | zero_sensors()
    > DONE
    ;
    """)
    initial_name = read_config(mock_file)
    bedroom = port.get_instance("Bedroom")
    with patch.object(bedroom, "get_value", return_value=1) as mock_get_value:
        assert bedroom.get_count() == 0
        event_processor(initial_name)
        assert bedroom.is_event_generating()
        assert bedroom.get_event_name() == 'ActiveSensor'
        assert bedroom.get_count() == 1
        assert port.get_instance('Window').get_count() == 0
        mock_get_value.assert_called_once()
        event_processor('zero')
        assert port.get_instance('Bedroom').get_count() == 0
