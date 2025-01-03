from abc import ABC, abstractmethod
import os
import RPi.GPIO as GPIO
import sys

from . import debug
from .event_queue import event_queue

# All ports
ports_by_name = dict()
ports_by_bcm = dict()
ports = []

if "pytest" in sys.modules:
    SENSORPATH='.'
else:
    SENSORPATH="/var/spool/alarm/sensor/"


def gpio_event_handler(channel):
    """
    Function registered to be called when a GPIO input rises.

    Args:
        channel (int): The port that fired.

    Returns:
        None
    """
    port = ports_by_bcm[channel]
    name = port.get_event_name()
    debug.log(f"Queuing sensor event {name}")
    event_queue.put(name)


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

        ports.append(self)
        ports_by_name[name] = self
        ports_by_bcm[self.bcm] = self
        debug.log(self)


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
    def is_relay(self):
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



    def set_bit(self, value):
        """Set the port to the specified value.
        Args:
            value (int): The value to set the port to (0 or 1).

        Returns:
            None
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
        self.log_when_disabled = False

        # Setup the hardware
        GPIO.setup(self.bcm, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.bcm, GPIO.RISING,
                              callback=gpio_event_handler, bouncetime=200)


    def is_event_generating(self):
        return bool(self.event_name)


    def is_sensor(self):
        return True


    def is_relay(self):
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


class ActuatorPort(Port):
    """An alarm system output port"""
    def __init__(self, name, pcb, physical, bcm, log):
        super().__init__(name, pcb, physical, bcm, log)

        # Setup the hardware
        GPIO.setup(self.bcm, GPIO.OUT, initial=GPIO.LOW)


    def is_sensor(self):
        return False


    def is_relay(self):
        return True


    def set_bit(self, value):
        GPIO.output(self.bcm, value)


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
    get_instance(name).set_bit(value)


def set_sensor_event(name, value):
    """
    Set the event name value of the sensor port with the specified name.

    Args:
        name (str): The identifier for the port's alarm purpose.
        value (str|None): The value to set the port event value.

    Returns:
        None
    """
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
        if not GPIO.input(port.get_bcm()):
            debug.log(f"{port} is not firing")
            continue
        with open(f"{SENSORPATH}/{port.get_name()}", "w") as file:
            pass
        port.increment_count()


def list_ports():
    """List available ports"""
    for port in ports:
        print(port.get_name() + ' (' + (
            'sensor)' if port.is_sensor() else 'actuator)'))
