import pytest
from io import StringIO
from unittest.mock import patch, call
import sys

from alarmd.dsl import read_config
from alarmd.state import event_processor
from alarmd import debug, port, event_queue


SETUP = """
# Required API functions
from os import system
from time import sleep
from sys import exit
from syslog import syslog, LOG_INFO, LOG_DEBUG, LOG_WARNING, closelog
from alarmd.port import increment_sensors, zero_sensors
from alarmd.port import set_bit, set_sensor_event

#Type	    PCB	PhysBCM	Log	Name
RELAY	    A1	29	5	1	Siren5
RELAY	    A2	29	6	0	Siren6

%i initial

DONE:
    ;
"""

SENSOR_SETUP = """
#Type	    PCB	PhysBCM	Log	Name
SENSOR	    S04	28	81	1	Bedroom
SENSOR	    S07	40	82	1	Window
"""

def test_entry_actions():
    mock_file = StringIO(SETUP + """
initial:
    | set_bit('Siren5', 1)
    | set_bit('Siren6', 0)
    > DONE
    ;
    """)
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2
        mock_output.assert_has_calls([call(5, 1), call(6, 0)])

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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2
        mock_output.assert_has_calls([call(5, 1), call(6, 0)])

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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        event_queue.put('go_second')
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2
        mock_output.assert_has_calls([call(5, 1), call(6, 0)])

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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        mock_output.assert_called_once_with(5, 1)

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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        mock_output.assert_called_once_with(5, 1)

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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2


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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2
        mock_output.assert_has_calls([call(5, 1), call(6, 0)])


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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        event_queue.put('go_second')
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2
        mock_output.assert_has_calls([call(5, 1), call(6, 0)])


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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 2
        mock_output.assert_has_calls([call(6, 0), call(5, 1)])

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
    with patch('RPi.GPIO.output') as mock_output, \
            patch('RPi.GPIO.setup') as mock_setup:
        event_queue.put('repeat')
        event_queue.put('repeat')
        event_queue.put('done')
        initial_name = read_config(mock_file)
        event_processor(initial_name)
        assert mock_output.call_count == 3


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
    > DONE
    ;
    """)
    with patch('RPi.GPIO.setup') as mock_setup:
        initial_name = read_config(mock_file)
        event_processor(initial_name)

def test_set_sensor_event():
    # Test the existence of the external API functions
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
    with patch('RPi.GPIO.setup') as mock_setup, \
            patch('RPi.GPIO.add_event_detect') as mock_add_event_detect:
        initial_name = read_config(mock_file)
        assert not port.get_instance('Bedroom').is_event_generating()
        event_processor(initial_name)
        assert port.get_instance('Bedroom').is_event_generating()
        event_processor('clear')
        assert not port.get_instance('Bedroom').is_event_generating()


def test_increment_sensors():
    # Test the existence of the external API functions
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
    with patch('RPi.GPIO.setup') as mock_setup, \
            patch('RPi.GPIO.add_event_detect') as mock_add_event_detect, \
            patch('RPi.GPIO.input', return_value=True) as mock_input:
        initial_name = read_config(mock_file)
        assert port.get_instance('Bedroom').get_count() == 0
        event_processor(initial_name)
        assert port.get_instance('Bedroom').is_event_generating()
        assert port.get_instance('Bedroom').get_event_name() == 'ActiveSensor'
        assert port.get_instance('Bedroom').get_count() == 1
        assert port.get_instance('Window').get_count() == 0
        mock_input.assert_called_once_with(81)
        event_processor('zero')
        assert port.get_instance('Bedroom').get_count() == 0


def test_trigger_sensor_event():
    # Test the existence of the external API functions
    mock_file = StringIO(SENSOR_SETUP + SETUP + """
initial:
    | set_sensor_event("Bedroom", "ActiveSensor")
# This should queue an ActiveSensor event
    | gpio_event_handler(81)
    > armed
    ;

armed:
    ActiveSensor > alarm
    done > DONE
    ;

alarm:
    | increment_sensors()
    > DONE
    ;
    """)
    with patch('RPi.GPIO.setup') as mock_setup, \
            patch('RPi.GPIO.add_event_detect') as mock_add_event_detect, \
            patch('RPi.GPIO.input', return_value=True) as mock_input:
        initial_name = read_config(mock_file)
        assert port.get_instance('Bedroom').get_count() == 0

        event_processor(initial_name)

        assert port.get_instance('Bedroom').get_event_name() == 'ActiveSensor'
        assert port.get_instance('Bedroom').get_count() == 1
