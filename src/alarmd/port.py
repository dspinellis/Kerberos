"""Abstract GPIO sensor and actuator ports."""

from abc import ABC, abstractmethod
from datetime import timedelta

# See https://libgpiod.readthedocs.io/en/latest/python_api.html
import os
import sys
import syslog
import threading

import gpiod

from alarmd.debug import Debug
from .event_queue import event_queue

CHIP_PATH = "/dev/gpiochip0"
DISABLEPATH = "/var/spool/alarm/disable/"

if "pytest" in sys.modules:
    SENSORPATH = "."
else:
    SENSORPATH = "/var/spool/alarm/sensor/"


class Port(ABC):
    """An alarm system I/O port abstract base class.
    This is used as a base class to document and specify the methods
    of the sensor and relay port subclasses."""

    # pylint: disable=too-many-public-methods

    # All ports
    ports_by_name = {}
    ports_by_bcm = {}
    ports = []

    # True when GPIO is emulated
    is_emulated = False

    # LineRequest
    # See https://libgpiod.readthedocs.io/en/latest/python_line_request.html
    request = None

    @classmethod
    def set_emulated(cls, value):
        """Set whether GPIO is emulated or not."""
        cls.is_emulated = value

    @classmethod
    def reset(cls):
        """Reset global variables to their default values."""
        cls.set_emulated(False)
        cls.ports_by_name.clear()
        cls.ports_by_bcm.clear()
        cls.ports.clear()

    @classmethod
    def get_instance_by_name(cls, name):
        """
        Return the port with the specified name.

        Args:
            name (str): The port's name

        Returns:
            Port: The object associated with the named port.
            None: If the name does not specify a known port.
        """
        return cls.ports_by_name.get(name)

    @classmethod
    def get_instance_by_bcm(cls, bcm):
        """
        Return the port with the specified bcm line offset.

        Args:
            bcm (int): The port's BCM line offset

        Returns:
            Port: The object associated with the named port.
            None: If the name does not specify a known port.
        """
        return cls.ports_by_bcm[bcm]

    @classmethod
    def request_lines(cls):
        """Setup and return all the port monitoring object.
        The object is set in this module to be used for port I/O.
        A thread is setup for monitoring and queuing port events.
        The returned object shall be used as a context to free to
        acquired resources.

        Args:
            None

        Returns:
            LineRequest : The LineRequest object for the configured ports.
        """
        # Obtain list of port configurations dicts
        port_configs = [port.gpiod_line_config() for port in cls.ports]
        # Convert it into a single dict
        config = {k: v for d in port_configs for k, v in d.items()}
        cls.request = gpiod.request_lines(
            CHIP_PATH, consumer="alarm", config=config
        )
        event_thread = threading.Thread(
            target=SensorPort.watch_line_value, args=[cls.request], daemon=True
        )
        event_thread.start()
        return cls.request

    @classmethod
    def list_ports(cls):
        """List available ports"""
        for port in cls.ports:
            print(
                port.get_name()
                + " ("
                + ("sensor)" if port.is_sensor() else "actuator)")
            )

    # pylint: disable-next=too-many-arguments
    def __init__(self, name, pcb, physical, bcm, _log):
        """
        Initialize a new I/O port instance.

        Args:
            name (str): The identifier for the port's alarm purpose.
            pcb (str): The mark on the printed circuit board.
            physical (int): The physical pin number associated with the port.
            bcm (int): The BCM (Broadcom) GPIO pin number.
            log (bool): Indicates whether logging is enabled for this port.

        Returns:
            None
        """

        self.name = name

        self.pcb = pcb
        self.physical = int(physical)
        self.bcm = int(bcm)
        self.emulated_value = None

        Port.ports.append(self)
        Port.ports_by_name[name] = self
        Port.ports_by_bcm[self.bcm] = self
        Debug.log(self)

    @abstractmethod
    def gpiod_line_config(self):
        """Return the port's gpiod configuration structure.
        Args:
            None

        Returns:
            dict: A single element dict with Line configuration suitable
                for passing to gpiod.request_lines config argument.
        """

    def is_event_generating(self):
        """Return true if the port is set to generate events.
        Args:
            None

        Returns:
            bool: True if the port is is set to generate events.
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    @abstractmethod
    def is_sensor(self):
        """Return true if the port is a sensor port.
        Args:
            None

        Returns:
            bool: True if the port is a sensor.
        """

    @abstractmethod
    def is_actuator(self):
        """Return true if the port is a relay port.
        Args:
            None

        Returns:
            bool: True if the port is a relay.
        """

    def get_name(self):
        """Return the port's name
        Args:
            None

        Returns:
            str: The port's name
        """
        return self.name

    def get_bcm(self):
        """Return the port's BCM pin number
        Args:
            None

        Returns:
            int: The port's BCM pin number
        """
        return self.bcm

    def set_emulated_value(self, value):
        """Set the emulated port to the specified value.
        Args:
            value (int): The value to set the port to (0 or 1).
            This is the value that get_value() will return.

        Returns:
            None
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def get_emulated_value(self):
        """Return the port's emulated value.
        This is the value that the port has been set to with set_value()
        Args:
            None

        Returns:
            int: The value to set the port to (0 or 1).
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def set_value(self, value):
        """Set the port to the specified value.
        Args:
            value (int): The value to set the port to (0 or 1).

        Returns:
            None
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def get_value(self):
        """Return the port's value.
        Args:
            None

        Returns:
            int: The value to set the port to (0 or 1).
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def set_event_name(self, value):
        """Set the sensor port to the specified event name value.
        Args:
            value (str|None): The value to set the port's generated events.

        Returns:
            None
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def get_event_name(self):
        """Return the sensor port's event name value.
        Args:

        Returns:
            str|None: The name of the port's generated event.
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def clear_count(self):
        """Clear the sensor port's fire counter value
        Args:
            None

        Returns:
            None
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def increment_count(self):
        """Increment the sensor port's fire counter value
        Args:
            None

        Returns:
            None
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")

    def get_count(self):
        """Return the sensor port's fire counter value
        Args:
            None

        Returns:
            int: Counter value
        """
        raise TypeError(f"Method not supported by {self.__class__.__name__}")


class SensorPort(Port):
    """An alarm system input port"""

    @classmethod
    def set_sensor_event(cls, name, value):
        """
        Set the event name value of the sensor port with the specified name.

        Args:
            name (str): The identifier for the port's alarm purpose.
            value (str|None): The value to set the port event value.

        Returns:
            None
        """
        if name == "*":
            for port in cls.ports:
                if port.is_sensor():
                    port.set_event_name(value)
        else:
            cls.get_instance_by_name(name).set_event_name(value)

    @classmethod
    def zero_sensors(cls):
        """Clear the count and file of all sensors."""
        for port in cls.ports:
            if not port.is_sensor():
                continue
            try:
                os.remove(f"{SENSORPATH}/{port.get_name()}")
            except FileNotFoundError:
                pass
            port.clear_count()

    @classmethod
    def increment_sensors(cls):
        """Increment the count and mark files for all event-generating
        and activity sensing sensors."""
        Debug.log("Incrementing sensors")
        for port in cls.ports:
            if not port.is_sensor():
                Debug.log(f"{port} is not sensor")
                continue
            if not port.is_event_generating():
                Debug.log(f"{port} is not generating events")
                continue
            if not port.get_value():
                Debug.log(f"{port} is not firing")
                continue
            file_path = f"{SENSORPATH}/{port.get_name()}"
            try:
                with open(file_path, "wb"):
                    pass
            except OSError as exc:
                syslog.syslog(
                    syslog.LOG_ERR, f"Failed to create {file_path}: {exc}"
                )
            port.increment_count()

    @classmethod
    def watch_line_value(cls, request):
        """
        Thread function to monitor GPIO input rises.

        Args:
            request (LineRequest ): The LineRequest object to monitor

        Returns:
            None
        """
        while True:
            # Blocks until at least one event is available
            for event in request.read_edge_events():
                port = Port.get_instance_by_bcm(event.line_offset)
                port_name = port.get_name()

                # Auto-disabled?
                if port.get_count() > 3:
                    syslog.syslog(
                        syslog.LOG_INFO,
                        f"trigger: {port_name} (auto-disabled)",
                    )
                    continue

                # Not enabled?
                event_name = port.get_event_name()
                if not event_name:
                    if port.is_always_logging():
                        syslog.syslog(
                            syslog.LOG_INFO, f"trigger: {port_name} (disabled)"
                        )
                    continue

                # Disabled by user file?
                if port.user_disabled():
                    syslog.syslog(
                        syslog.LOG_INFO,
                        f"trigger: {port_name} (user-disabled)",
                    )
                    continue

                Debug.log(f"Queueing {event_name=} for {port_name=}")
                event_queue.put(event_name)

    @classmethod
    def sensor_display(cls):
        """List available ports"""
        for port in cls.ports:
            if not port.is_sensor():
                continue
            print(f"{port.get_name()}: {port.get_value()}")

    # This is called by parsing a nicely formatted DSL table,
    # so number of arguments isn't a big concern.
    # pylint: disable-next=too-many-positional-arguments,too-many-arguments
    def __init__(self, name, pcb, physical, bcm, log):
        # pylint: disable-next=too-many-arguments,too-many-positional-arguments
        super().__init__(name, pcb, physical, bcm, log)

        # The name of the events to generate, or None
        self.event_name = None

        # Number of times the sensor has raised an alarm
        # Incremented on alarms and auto-disabled when it reaches
        # AUTO_DISABLE_COUNT
        self.count = 0

        # True to log triggers when disabled
        # Was log_when_disabled in the C version
        self.always_logging = bool(log)

    def gpiod_line_config(self):
        return {
            self.bcm: gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT,
                bias=gpiod.line.Bias.PULL_UP,
                edge_detection=gpiod.line.Edge.RISING,
                debounce_period=timedelta(milliseconds=200),
            )
        }

    def is_always_logging(self):
        """Return true if the sensor is logging even when disabled."""
        return self.always_logging

    def is_event_generating(self):
        """Return true if the sensor has an event associated with it."""
        return bool(self.event_name)

    def is_sensor(self):
        """Return true if the port is associated with a sensor."""
        return True

    def is_actuator(self):
        """Return true if the port is associated with an actuator."""
        return False

    def set_event_name(self, value):
        """Set the sensor to trigger the specified event."""
        self.event_name = value

    def get_event_name(self):
        """Return the event associated with the sensor, if any."""
        return self.event_name

    def clear_count(self):
        """Clear the number of times the sensor has been triggered."""
        self.count = 0

    def increment_count(self):
        """Increment the number of times the sensor has been triggered."""
        self.count += 1

    def get_count(self):
        """Return the number of times the sensor has been triggered."""
        return self.count

    def get_value(self):
        """Return the sensor's input value."""
        if Port.is_emulated:
            return self.emulated_value
        return (
            1
            if Port.request.get_value(self.bcm) == gpiod.line.Value.ACTIVE
            else 0
        )

    def set_emulated_value(self, value):
        """Set the sensor's emulated value."""
        if Port.is_emulated:
            self.emulated_value = value
        else:
            raise RuntimeError("Ports are not emulated.")

    def user_disabled(self):
        """
        Return True if the port has been externally disabled by the user.

        Returns:
            bool: True if the file exists, indicating the port is disabled.
        """
        file_path = os.path.join(DISABLEPATH, self.get_name())
        return os.path.exists(file_path)


class ActuatorPort(Port):
    """An alarm system output port"""

    @classmethod
    def set_bit(cls, name, value):
        """
        Set the port with the specified name to the specified value.

        Args:
            name (str): The identifier for the port's alarm purpose.
            value (int): The value to set the port to (0 or 1).

        Returns:
            None
        """
        cls.get_instance_by_name(name).set_value(value)

    def gpiod_line_config(self):
        return {
            self.bcm: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE,
            )
        }

    def is_sensor(self):
        return False

    def is_actuator(self):
        return True

    def set_value(self, value):
        if Port.is_emulated:
            self.emulated_value = value
        else:
            syslog.syslog(
                syslog.LOG_INFO, f"set {self.name} {'on' if value else 'off'}"
            )
            Port.request.set_value(
                self.bcm,
                (
                    gpiod.line.Value.ACTIVE
                    if value
                    else gpiod.line.Value.INACTIVE
                ),
            )

    def get_emulated_value(self):
        if Port.is_emulated:
            return self.emulated_value
        raise RuntimeError("Ports are not emulated.")
