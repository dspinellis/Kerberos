import pytest
from io import StringIO
from unittest.mock import patch, call

from alarmd.dsl import read_config
from alarmd.port import get_instance, set_bit
from alarmd import state

def test_read_config_sensor_port():
    #                     Type	    PCB	PhysBCM	Log	Name
    mock_file = StringIO("SENSOR	S02	26	7	1	Entrance\n")
    read_config(mock_file)
    port = get_instance("Entrance")
    assert port.is_sensor()
    assert port.is_always_logging()
    assert port.get_bcm() == 7


def test_read_config_actuator_port():
    #                     Type	        PCB	PhysBCM	Log	Name
    mock_file = StringIO("ACTUATOR	    A1	29	5	1	Siren0")
    read_config(mock_file)
    port = get_instance("Siren0")
    assert port.is_actuator()
    assert port.get_bcm() == 5


def test_read_entry_actions():
    mock_file = StringIO("""astate:
    | first()
    | second()
    | call astate2
    | syslog(LOG_DEBUG, "entered")
    |=1 syslog(LOG_INFO, "phone")
    | ClearCounter(day_alarm)

    ;
    """)
    read_config(mock_file)

    assert state.get_instance("astate").get_entry_action(0) == "first()"
    assert state.get_instance("astate").get_entry_action(1) == "second()"
    assert state.get_instance("astate").get_entry_action(2) == 'get_instance("astate2").enter()'
    assert state.get_instance("astate").get_entry_action(3) == 'syslog(LOG_DEBUG, "entered")'
    assert state.get_instance("astate").get_entry_action(4) == 'syslog(LOG_INFO, "phone") if self.counter ==1 else None'
    assert state.get_instance("astate").get_entry_action(5) == 'get_instance("day_alarm").clear_counter()'


def test_read_multiple_states():
    mock_file = StringIO("""
*:
    disarm > live
    ;

astate1:
    | first()
    ;
astate2:
    | second()
    ;
    """)
    read_config(mock_file)

    assert state.get_instance("*").get_event_transition('disarm') == 'live'
    assert state.get_instance("astate1").get_entry_action(0) == "first()"
    assert state.get_instance("astate2").get_entry_action(0) == "second()"


def test_read_plain_transition():
    mock_file = StringIO("""astate:
    disarm > living
    arm > armed
    ;
    """)
    read_config(mock_file)

    new_state = state.get_instance("astate").get_event_transition('disarm')
    assert new_state == 'living'
    new_state = state.get_instance("astate").get_event_transition('arm')
    assert new_state == 'armed'


def test_read_timer_transition():
    mock_file = StringIO("""astate:
    10s > living
    ;
    """)
    read_config(mock_file)

    new_state = state.get_instance("astate").get_event_transition('TIMER_10')
    assert new_state == 'living'
    registration = state.get_instance("astate").get_entry_action(0)
    assert registration == "register_timer_event(10, 'TIMER_10')"


def test_initial_state():
    mock_file = StringIO("""%i initial

initial:
    ;
    """)
    initial_name = read_config(mock_file)
    assert initial_name == 'initial'


def test_python_block():
    mock_file = StringIO("""%{
a = 42
%}
    """)
    read_config(mock_file)

    assert eval('a', state.__dict__) == 42
