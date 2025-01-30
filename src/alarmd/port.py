from abc import ABC, abstractmethod
# See https://libgpiod.readthedocs.io/en/latest/python_api.html
import gpiod
import os
import sys
import syslog
import threading
from datetime import timedelta

from . import debug
from .event_queue import event_queue

# All ports
ports_by_name = dict()
ports_by_bcm = dict()
ports = []

# True when GPIO is emulated
is_emulated = False

# LineRequest
# See https://libgpiod.readthedocs.io/en/latest/python_line_request.html
request = None

CHIP_PATH = "/dev/gpiochip0"
DISABLEPATH = "/var/spool/alarm/disable/"


def set_emulated(value):
    """Set whether GPIO is emulated or not."""
    global is_emulated
    is_emulated = value


def reset_globals():
    """Reset global variables to their default values."""
    set_emulated(False)
    ports_by_name.clear()
    ports_by_bcm.clear()
    ports.clear()


if "pytest" in sys.modules:
    SENSORPATH='.'
else:
    SENSORPATH="/var/spool/alarm/sensor/"


def watch_line_value(request):
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
            port = ports_by_bcm[event.line_offset]
            port_name = port.get_name()

            # Auto-disabled?
            if port.get_count() > 3:
                syslog.syslog(syslog.LOG_INFO, f"trigger: {port_name} (auto-disabled)")
                continue

            # Not enabled?
            event_name = port.get_event_name()
            if not event_name:
                if port.is_always_logging():
                    syslog.syslog(syslog.LOG_INFO, f"trigger: {port_name} (disabled)")
                continue

            # Disabled by user file?
            if port.user_disabled():
                syslog.syslog(syslog.LOG_INFO, f"trigger: {port_name} (user-disabled)")
                continue

            debug.log(f"Queueing {event_name=} for {port_name=}")
            event_queue.put(event_name)


class Port(ABC):
    """An alarm system I/O port abstract base class.
    This is used as a base class to document and specify the methods
    of the sensor and relay port subclasses."""
    def __init__(self, name, pcb, physical, bcm, log):
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

        ports.append(self)
        ports_by_name[name] = self
        ports_by_bcm[self.bcm] = self
        debug.log(self)


    @abstractmethod
    def gpiod_line_config(self):
        """Return the port's gpiod configuration structure.
        Args:
            None

        Returns:
            dict: A single element dict with Line configuration suitable
                for passing to gpiod.request_lines config argument.
        """
        pass


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
        pass



    @abstractmethod
    def is_actuator(self):
        """Return true if the port is a relay port.
        Args:
            None

        Returns:
            bool: True if the port is a relay.
        """
        pass



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
    def __init__(self, name, pcb, physical, bcm, log):
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
        return self.always_logging


    def is_event_generating(self):
        return bool(self.event_name)


    def is_sensor(self):
        return True


    def is_actuator(self):
        return False


    def set_event_name(self, value):
        self.event_name = value


    def get_event_name(self):
        return self.event_name


    def clear_count(self):
        self.count = 0


    def increment_count(self):
        self.count += 1


    def get_count(self):
        return self.count


    def get_value(self):
        if is_emulated:
            return self.emulated_value
        else:
            return 1 if request.get_value(self.bcm) == gpiod.line.Value.ACTIVE else 0


    def set_emulated_value(self, value):
        if is_emulated:
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
    def __init__(self, name, pcb, physical, bcm, log):
        super().__init__(name, pcb, physical, bcm, log)


    def gpiod_line_config(self):
        return {
            self.bcm: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE
            )
        }


    def is_sensor(self):
        return False


    def is_actuator(self):
        return True


    def set_value(self, value):
        if is_emulated:
            self.emulated_value = value
        else:
            syslog.syslog(syslog.LOG_INFO,
                          f"set {self.name} {'on' if value else 'off'}")
            request.set_value(self.bcm, gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE)


    def get_emulated_value(self):
        if is_emulated:
            return self.emulated_value
        else:
            raise RuntimeError("Ports are not emulated.")


def get_instance(name):
    """
    Return the port with the specified name.

    Args:
        name (str): The port's name

    Returns:
        Port: The object associated with the named port.
        None: If the name does not specify a known port.
    """
    return ports_by_name.get(name)


def set_bit(name, value):
    """
    Set the port with the specified name to the specified value.

    Args:
        name (str): The identifier for the port's alarm purpose.
        value (int): The value to set the port to (0 or 1).

    Returns:
        None
    """
    get_instance(name).set_value(value)


def set_sensor_event(name, value):
    """
    Set the event name value of the sensor port with the specified name.

    Args:
        name (str): The identifier for the port's alarm purpose.
        value (str|None): The value to set the port event value.

    Returns:
        None
    """
    if name == '*':
        for p in ports:
            if p.is_sensor():
                p.set_event_name(value)
    else:
        get_instance(name).set_event_name(value)


def zero_sensors():
    """Clear the count and file of all sensors."""
    for port in ports:
        if not port.is_sensor():
            continue
        try:
            os.remove(f"{SENSORPATH}/{port.get_name()}")
        except FileNotFoundError:
            pass
        port.clear_count()


def increment_sensors():
    """Increment the count and mark files for all event-generating
    and activity sensing sensors."""
    debug.log('Incrementing sensors')
    for port in ports:
        if not port.is_sensor():
            debug.log(f"{port} is not sensor")
            continue
        if not port.is_event_generating():
            debug.log(f"{port} is not generating events")
            continue
        if not port.get_value():
            debug.log(f"{port} is not firing")
            continue
        file_path = f"{SENSORPATH}/{port.get_name()}"
        try:
            with open(file_path, "w") as file:
                pass
        except OSError as e:
            syslog.syslog(syslog.LOG_ERR, f"Failed to create {file_path}: {e}")
        port.increment_count()


def list_ports():
    """List available ports"""
    for port in ports:
        print(port.get_name() + ' (' + (
            'sensor)' if port.is_sensor() else 'actuator)'))


def request_lines():
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
    global request
    # Obtain list of port configurations dicts
    port_configs=[port.gpiod_line_config() for port in ports]
    # Convert it into a single dict
    config = {k: v for d in port_configs for k, v in d.items()}
    request = gpiod.request_lines(
        CHIP_PATH,
        consumer="alarm",
        config=config
    )
    event_thread = threading.Thread(target=watch_line_value, args=[request], daemon=True)
    event_thread.start()
    return request
