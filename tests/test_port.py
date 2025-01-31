import pytest
from unittest.mock import patch, MagicMock, mock_open

from alarmd import debug, port
from alarmd.port import ActuatorPort, Port, SensorPort


@pytest.fixture(autouse=True)
def reset_globals():
    """Fixture to reset global variables before each test."""
    Port.reset()
    Port.set_emulated(True)


def test_sensor_port_initialization():
    """Test SensorPort initialization."""
    sensor = SensorPort("TestSensor", "P1", 1, 17, True)
    assert sensor.get_name() == "TestSensor"
    assert sensor.is_sensor()
    assert not sensor.is_actuator()


def test_actuator_port_initialization():
    """Test ActuatorPort initialization."""
    actuator = ActuatorPort("TestActuator", "P2", 2, 18, True)
    assert actuator.get_name() == "TestActuator"
    assert not actuator.is_sensor()
    assert actuator.is_actuator()


def test_set_emulated():
    """Test setting GPIO emulation mode."""
    Port.set_emulated(True)
    assert Port.is_emulated

    Port.set_emulated(False)
    assert not Port.is_emulated


def test_get_instance():
    """Test retrieving a port instance by name."""
    assert len(Port.ports) == 0
    sensor = SensorPort("TestSensor", "P1", 1, 17, True)
    assert Port.get_instance_by_name("TestSensor") == sensor
    assert Port.get_instance_by_name("NonExistentPort") is None
    assert len(Port.ports) == 1


def test_set_bit():
    """Test setting port value using set_bit."""
    actuator = ActuatorPort("TestActuator", "P2", 2, 18, True)

    with patch.object(ActuatorPort, "set_value") as mock_set_value:
        Port.set_emulated(False)
        ActuatorPort.set_bit("TestActuator", 1)
        mock_set_value.assert_called_once_with(1)


def test_set_sensor_event():
    """Test setting event name of a sensor port."""
    sensor = SensorPort("TestSensor", "P1", 1, 17, True)
    SensorPort.set_sensor_event("TestSensor", "FireAlarm")
    assert sensor.get_event_name() == "FireAlarm"


def test_zero_sensors():
    """Test clearing all sensor counts and removing sensor files."""
    with patch("alarmd.port.os.remove") as mock_remove:
        sensor = SensorPort("TestSensor", "P1", 1, 17, True)
        sensor.set_event_name("AlarmTriggered")
        sensor.increment_count()

        assert sensor.get_count() == 1
        SensorPort.zero_sensors()
        assert sensor.get_count() == 0
        mock_remove.assert_called_once()


def test_increment_sensors_firing():
    """Test incrementing sensors that are firing."""
    with patch("alarmd.port.open", mock_open()) as mock_file:
        sensor = SensorPort("TestSensor", "P1", 1, 17, True)
        sensor.set_event_name("AlarmTriggered")
        sensor.set_emulated_value(1)

        SensorPort.increment_sensors()
        assert sensor.get_count() == 1
        mock_file.assert_called_once_with(
            f"{port.SENSORPATH}/TestSensor", "wb"
        )


def test_increment_sensors_not_firing():
    """Test incrementing sensors that are firing."""
    with patch("alarmd.port.open", mock_open()) as mock_file:
        sensor = SensorPort("TestSensor", "P1", 1, 17, True)
        sensor.set_event_name("AlarmTriggered")
        sensor.set_emulated_value(0)

        SensorPort.increment_sensors()
        assert sensor.get_count() == 0


def test_list_ports(capsys):
    """Test listing available ports."""
    port1 = SensorPort("TestSensor1", "P1", 1, 17, True)
    port2 = ActuatorPort("TestActuator", "P2", 2, 18, True)

    Port.list_ports()

    captured = capsys.readouterr()
    assert "TestSensor1 (sensor)" in captured.out
    assert "TestActuator (actuator)" in captured.out
