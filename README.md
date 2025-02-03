# Kerberos DSL-Configurable Burglar Alarm System
 
Kerberos is a highly-flexible burglar alarm system for the *Raspberry Pi*.
It is configurable through a domain-specific language
and arbitrary C functions.
It was originally designed and implemented to run under FreeBSD using
the *pbio*(4) 8255 parallel peripheral interface basic I/O driver,
with an interface such as the Advantech PCL-724 Digital I/O Card.
It was later modified to run on a *Raspberry Pi* with the
*Wiring Pi* API.
In both cases a custom-built PCB interfaces the alarm system to
passive infrared (PIR), magnetic, and other sensors as well as
to actuators, such as sirens.

Note that configuring and deploying Kerberos requires significant
hardware, programming, security, and system administration skills.
The code and documentation provided here, is just to get you started,
it is by no means a turnkey solution.

## Configuration
To configure Kerberos pick a name for your configuration,
say *acme*, and create three files.

* `acme-io.h` specifies the Kerberos's sensors and actuators.
* `acme.alr` specifies the Kerberos's rules as state transitions.
  For example, it can specify that in the *armed* state a movement
  in the bedroom will make it enter the *intruder* state and sound
  a siren.
* `acme-cmd.h` specifies the names of Kerberos's user commands (e.g. disarm).

One set of simple and one set of more sophisticated example files are provided,
but the possibilities of what you can do are limitless.
Here are some ideas.

* Kerberos can send notifications using cellular SMS, a voice modem,
  web push notifications, or email.
* Kerberos can filter-out spurious movements.
* Kerberos can warn you through a home appliance, such as Alexa,
  before it raises hell in the neighborhood.
* Kerberos can automatically disarm based on IoT signals.
* Kerberos can be operated and monitored through a web interface or a phone app.
* Kerberos can automatically enter diverse states at specific times
  through *cron*(8) jobs.
* Kerberos can enter diverse states based on movement patterns.

## A Note on Safety and Security
Although setting up Kerberos may appear to be a fun hobby project,
note that the safety of yourself, your loved ones, and your property may
end up depending on it.
Moreover, spurious alarms can distress your neighbours and get you
into trouble with law enforcement authorities.
(In some countries a spurious alarm call to the police results in a steep
fine.)
Finally consider that the Kerberos's operation may face determined
opponents who may use any possible means,
including physical force and violence, to neuter it.
Consequently, you need to carefully verify and validate your setup and
your operations.
This includes careful design and planning, exhaustive testing,
and also training of the people who will be using the system.
In your design think about the Kerberos's
physical access control,
backup power and communications links,
watchdog monitoring, and
tamper alarms.
If your system running Kerberos will be accessible over the internet,
you need to harden it against intrusions and denial of service attacks.

Pay special attention to the following two sections of the
Kerberos's license agreement.

###  15. Disclaimer of Warranty.
  **THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.**

###  16. Limitation of Liability.

  **IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.**

## Building and Deployment
* Download, build, and install the [WiringPi](http://wiringpi.com/) API.
* Build the system by running `make`.
* Install the generated alarm daemon and command-line interface by running
  `sudo make install`.
* Configure logging so as to monitor Kerberos's operation.
  Here is an example configuration for *rsyslogd*(8),
  which you could place in `/etc/rsyslog.d/alarm.conf`.

```
# Administrative information
if $programname == 'alarm' and $syslogseverity-text == 'info' then /var/log/alarm.log

# Exhaustive alarm sensor logging (included in debug messages)
if $programname == 'alarm' then /var/log/radar.log

# Discard information and debug so that they don't go anywhere else
# (Does not work with rsyslogd 5.8.11
#if $syslogseverity >= 6 and $programname == 'alarm' then ~

# Discard all alarm messages
if $programname == 'alarm' then ~
```

* Configure alarm log rotation.
  Here is an example of a  *logrotate*(8) configuration file,
  which you could place in `/etc/logrotate.d/alarm`.

```
/var/log/radar.log {
        daily
        rotate 22000
        olddir archive/radar
        dateext
        dateyesterday
        missingok
        compress
        delaycompress
        sharedscripts
        postrotate
                invoke-rc.d rsyslog rotate > /dev/null
        endscript
}

/var/log/alarm.log {
        monthly
        rotate 1200
        olddir archive/alarm
        dateext
        dateformat "-%Y%m"
        dateyesterday
        missingok
        compress
        delaycompress
        sharedscripts
        postrotate
                invoke-rc.d rsyslog rotate > /dev/null
        endscript
}
```

* Kerberos runs as a service named *alarm* through an installed *initd* script.
  Enable the service to run at startup and start it up.
* Create the following directories:
      * `/var/spool/alarm/cmd/`: communication between the command-line
        interface *alarm* and the daemon.
      * `/var/spool/alarm/disable/`: names of manually disabled sensors
      * `/var/spool/alarm/sensor/`: sensor trigger counts
      * `/var/spool/alarm/status/`: Kerberos's status
* You send commands to the daemon through the command-line *alarm* program.
  This creates files in the `/var/spool/alarm/cmd/` directory.
  Configure the directory's permissions and have *cmd* run with the
  appropriate permissions (e.g. through *sudo*(1) or by
  having *alarm* run with setuid permissions),
  so that this scheme will work securely.

## Operation
In the form provided you operate Kerberos with the *alarm* command,
which accepts the commands that you configured.
You monitor Kerberos's operation through the configured log files,
e.g. with `tail -F /var/log/radar.log`.
You will most probably want to setup a more user-friendly
interface based on these two facilities.

## Development processes
At the top level directory you can perform the following actions.

Install developer dependencies with
```sh
pip install -r requirements-dev.txt
```


Format code with:
```sh
find tests src -name '*.py' | xargs black -l 79
```

Run static analysis checks with:
```sh
find src -name '*.py' | xargs python -m pylint

Run unit tests with:
```sh
pytest -s tests/
```

Even better configure to run the supplied Git pre-commit hook
```sh
git config core.hooksPath .githooks
```

# See Also
* Diomidis Spinellis. [The information furnace: Consolidated home control](http://www.dmst.aueb.gr/dds/pubs/jrnl/2003-PUC-ifurnace/html/furnace.html). Personal and Ubiquitous Computing, 7(1):53–69, 2003. [doi:10.1007/s00779-002-0213-8](http://dx.doi.org/10.1007/s00779-002-0213-8)
* [ZoneMinder](http://www.zoneminder.com/)
