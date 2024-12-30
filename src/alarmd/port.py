import os
import RPi.GPIO as GPIO
import sys

from . import debug, event_queue

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

    print(f"Interrupt detected on pin {channel}")


class Port:
    """Details about an alarm system I/O port"""
    def __init__(self, name, io_type, pcb, physical, bcm, log):
        """
        Initialize a new I/O port instance.

        Args:
            name (str): The identifier for the port's alarm purpose.
            io_type (str): The type of input/output: SENSOR or RELAY.
            pcb (str): The mark on the printed circuit board.
            physical (int): The physical pin number associated with the port.
            bcm (int): The BCM (Broadcom) GPIO pin number.
            log (bool): Indicates whether logging is enabled for this port.

        Returns:
            None
        """

        self.name = name

        self.io_type = io_type
        self.pcb = pcb
        self.physical = int(physical)
        self.bcm = int(bcm)
        self.log = bool(int(log))

        # A value of ACTIVE, DELAYED, PERIMETER for sensors that generate events
        self.active = None

        # Number of times the sensor has raised an alarm
        # Incremented on alarms and auto-disabled when it reaches
        # AUTO_DISABLE_COUNT
        self.count = 0

        # True to log triggers when disabled
        self.log_when_disabled = False

        # Setup the hardware
        if io_type == 'SENSOR':
            GPIO.setup(self.bcm, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.bcm, GPIO.RISING,
                                  callback=gpio_event_handler, bouncetime=200)
        elif io_type == 'RELAY':
            GPIO.setup(self.bcm, GPIO.OUT, initial=GPIO.LOW)
        else:
            raise ValueError(f"Illegal io_type {io_type}: must be SENSOR or RELAY")
        ports.append(self)
        ports_by_name[name] = self
        ports_by_bcm[self.bcm] = self
        debug.log(self)


    def is_active(self):
        """Return true if the port is active.
        Args:
            None

        Returns:
            bool: True if the port is active.
        """
        return bool(self.active)



    def is_sensor(self):
        """Return true if the port is a sensor port.
        Args:
            None

        Returns:
            bool: True if the port is a sensor.
        """
        return self.io_type == 'SENSOR'



    def is_relay(self):
        """Return true if the port is a relay port.
        Args:
            None

        Returns:
            bool: True if the port is a relay.
        """
        return self.io_type == 'RELAY'



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
        if not self.is_relay():
            raise ValueError(f"Illegal write to non-relay port {self.name}")
        GPIO.output(self.bcm, value)


    def set_active(self, value):
        """Set the sensor port to the specified active value.
        Args:
            value (str|None): The value to set the port active field.

        Returns:
            None
        """
        if not self.is_sensor():
            raise ValueError(f"Illegal active setting to non-sensor port {self.name}")
        self.active = value


    def get_active(self):
        """Return the sensor port's active value.
        Args:

        Returns:
            str|None: The value of the port's active field.
        """
        if not self.is_sensor():
            raise ValueError(f"Illegal active setting to non-sensor port {self.name}")
        return self.active


    def clear_count(self):
        """Clear the sensor port's fire counter value
        Args:
            None

        Returns:
            None
        """
        if self.io_type != "SENSOR":
            raise ValueError(f"Counter access to non-sensor port {self.name}")
        self.count = 0


    def increment_count(self):
        """Increment the sensor port's fire counter value
        Args:
            None

        Returns:
            None
        """
        if self.io_type != "SENSOR":
            raise ValueError(f"Counter access to non-sensor port {self.name}")
        self.count += 1


    def get_count(self):
        """Return the sensor port's fire counter value
        Args:
            None

        Returns:
            int: Counter value
        """
        if self.io_type != "SENSOR":
            raise ValueError(f"Counter access to non-sensor port {self.name}")
        return self.count


def get_instance(name):
    """
    Return the port with the specified name.

    Args:
        name (str): The port's name

    Returns:
        Port: The object associated with the named port.
    """
    return ports_by_name[name]


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


def set_sensor_active(name, value):
    """
    Set the active value of the port with the specified name.

    Args:
        name (str): The identifier for the port's alarm purpose.
        active (str|None): The value to set the port active value.

    Returns:
        None
    """
    get_instance(name).set_active(value)


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
    """Increment the count and mark files for all active and sensing sensors."""
    debug.log('Incrementing sensors')
    for port in ports:
        if not port.is_sensor():
            debug.log(f"{port} is not sensor")
            continue
        if not port.is_active():
            debug.log(f"{port} is not active")
            continue
        if not GPIO.input(port.get_bcm()):
            debug.log(f"{port} is not firing")
            continue
        with open(f"{SENSORPATH}/{port.get_name()}", "w") as file:
            pass
        port.increment_count()
