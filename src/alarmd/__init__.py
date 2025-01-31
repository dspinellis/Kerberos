"""Make port functions directly visible to the DSL without class prefix."""

from .port import ActuatorPort, Port, SensorPort

# pylint: disable=invalid-name
is_emulated = Port.is_emulated

set_bit = ActuatorPort.set_bit

increment_sensors = SensorPort.increment_sensors
set_sensor_event = SensorPort.set_sensor_event
zero_sensors = SensorPort.zero_sensors
