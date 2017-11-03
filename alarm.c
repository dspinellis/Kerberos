/*
 * Home alarm interface program
 * Requires the pbio driver
 *
 * (C) Copyright 2000, 2001 Diomidis Spinellis.  All rights reserved.
 *
 * $Id: alarm.c,v 1.16 2012/02/15 16:58:12 dds Exp $
 *
 */

#include "/sys/sys/pbioio.h"
#include <fcntl.h>
#include <assert.h>
#include <stdio.h>
#include <time.h>
#include <syslog.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>

#include "evlst.h"
#include "alarm.h"
#include "cmd.h"

void
errexit(char *s)
{
	syslog(LOG_ERR, "%s: %m", s);
	closelog();
	exit(1);
}

enum e_port {
	PA, PB, PCH, PCL
};

enum e_fun {
	SENSE, OUTPUT
};

struct s_bit {
	char *pcbname;		/* Name on the PCB */
	enum e_port port;	/* I/O port offset on the card */
	int bit;		/* Bit on the port */
	enum e_fun fun;		/* SENSE / OUTPUT */
	char *name;		/* Human-readable name */
	int event;		/* Event to raise */
	int val;		/* Virtualized bit value */
	int active;		/* For sensors, set to true when they have to
				 * generate events (ACTIVE, DELAYED) */
	int count;		/* Number of times the sensor has raised an
				 * alarm */
} bit[] = {
#include "alarm-spec.h"
};

#define NUM_BIT (sizeof(bit) / sizeof(struct s_bit))

struct s_port {
	char *name;
	int omode;
	int fd;
} port[] = {
	{"/dev/pbio0a", O_RDONLY},
	{"/dev/pbio0b", O_RDWR},
	{"/dev/pbio0ch", O_RDONLY},
	{"/dev/pbio0cl", O_RDONLY},
};

#define NUM_PORT (sizeof(port) / sizeof(struct s_port))

void
set_sensor_active(char *name, int val)
{
	int i;
	int found = 0;

	for (i = 0; i < NUM_BIT; i++)
		if (name == NULL || (strcmp(bit[i].name, name) == 0)) {
			bit[i].active = val;
			found = 1;
		}
	assert(found);
}

/*
 * Zero the count of all sensors
 */
void
zero_sensors(void)
{
	int i;
	char buff[1024];

	for (i = 0; i < NUM_BIT; i++) {
		strcpy(buff, SENSORPATH);
		strcat(buff, bit[i].name);
		(void)unlink(buff);
		bit[i].count = 0;
	}
}

/*
 * Increment the count of all sensors that are on and active 
 * Create a corresponding file in the sensor directory
 */
void
increment_sensors(void)
{
	int i, fd;
	char buff[1024];

	for (i = 0; i < NUM_BIT; i++)
		if (bit[i].fun == SENSE && bit[i].active && bit[i].val) {
			bit[i].count++;
			strcpy(buff, SENSORPATH);
			strcat(buff, bit[i].name);
			if ((fd = open(buff, O_CREAT | O_TRUNC | O_WRONLY, 0444)) < 0)
				syslog(LOG_ERR, "%s: %m", buff);
			else
				close(fd);
		}
}

/*
 * Return true if a given sense port has been externaly disabled by the user
 */
int
user_disabled(int i)
{
	char buff[1024];

	strcpy(buff, DISABLEPATH);
	strcat(buff, bit[i].name);
	return ((access(buff, F_OK) == 0) ? 1 : 0);
}

void
set_bit(char *name, int val)
{
	int i;
	unsigned char vo;

	if (memcmp(name, "Led", 3) != 0)
		syslog(LOG_INFO, "set %s %s", name, val ? "on" : "off");
	for (i = 0; i < NUM_BIT; i++) {
		if (bit[i].fun != OUTPUT)
			continue;
		if (strcmp(bit[i].name, name) == 0) {
			if (read(port[bit[i].port].fd, &vo, 1) < 0)
				errexit("read");
			if (val)
				vo |= bit[i].bit;
			else
				vo &= ~bit[i].bit;
			if (write(port[bit[i].port].fd, &vo, 1) < 0)
				errexit("write");
			return;
		}
	}
	assert(0);
}

void
setall(int val)
{
	int i;
	unsigned char vo;
	int oport;

	oport = -1;
	for (i = 0; i < NUM_BIT; i++) {
		if (bit[i].fun != OUTPUT)
			continue;
		if (oport != bit[i].port) {
			if (read(port[bit[i].port].fd, &vo, 1) < 0)
				errexit("read");
			oport = bit[i].port;
		}
		if (val)
			vo |= bit[i].bit;
		else
			vo &= ~bit[i].bit;
		if (write(port[bit[i].port].fd, &vo, 1) < 0)
			errexit("write");
	}
}

static int timer_event = -1;
static int timer_interval;
static time_t timer_start;

/*
 * Register an event to be produced after interval seconds
 */
void
register_timer_event(int interval, int event)
{
	timer_event = event;
	timer_interval = interval;
	time(&timer_start);
}

/*
 * The values of the red and green LEDs
 */
static int led_green;
static int led_red;

void
set_led(int green, int red)
{
	led_green = green;
	led_red = red;
}

/* Concatenate the specified formatted string to the log buffer */
#define logcatf(fmt, val) {\
	int n = snprintf(buffp, sizeof(buff) - (buffp - buff), fmt, val); \
	if (n < 0) { \
		strcpy(buff + sizeof(buff) - 4, "..."); \
		buffp = buff + sizeof(buff); \
	} else \
		buffp += n; \
} while(0);

int
get_event(void)
{
	int i;
	unsigned char vi;
	int iport;
	static int ev_queue[NUM_BIT + 10];
	static int ev_count = 0;
	static int flash = 0;
	time_t now;
	char buff[512];
	char *buffp;

	for (;;) {
		set_bit("Led1", led_red ? flash : 1);
		set_bit("Led2", led_green ? flash : 1);
		flash = !flash;

		/* If there is a queued event, return it */
		if (ev_count)
			return (ev_queue[--ev_count]);

		/* Check for commands */
		for (i = 0; i < NUM_CMD; i++)
			if (access(cmd[i].fname, F_OK) == 0) {
				unlink(cmd[i].fname);
				/* Don't queue! */
				syslog(LOG_INFO, "command: %s", cmd[i].name);
				return (cmd[i].event);
			}

		/* Check for elapsed timers */
		if (timer_event != -1) {
			time(&now);
			if (difftime(now, timer_start) >= timer_interval) {
				syslog(LOG_DEBUG, "elapsed interval: %d", timer_interval);
				ev_queue[ev_count++] = timer_event;
				timer_event = -1;
				/* To return the event */
				continue;
			}
		}

		/* Check ports for an active sensor and queue events */
		iport = -1;
		buffp = buff;
		for (i = 0; i < NUM_BIT; i++) {
			if (bit[i].fun != SENSE)
				continue;
			if (iport != bit[i].port) {
				if (read(port[bit[i].port].fd, &vi, 1) < 0)
					errexit("read");
				iport = bit[i].port;
			}
			if (vi & bit[i].bit) {
				if (bit[i].count > 3) {
					logcatf(" %s (auto-disabled)", bit[i].name);
					continue;
				} else if (!bit[i].active) {
					logcatf(" %s (disabled)", bit[i].name);
					continue;
				} else if (user_disabled(i)) {
					logcatf(" %s (user-disabled)", bit[i].name);
					continue;
				} else
					logcatf(" %s", bit[i].name);
				switch (bit[i].active) {
				case ACTIVE:
					ev_queue[ev_count++] = EV_ActiveSensor;
					break;
				case DELAYED:
					ev_queue[ev_count++] = EV_DelayedSensor;
					break;
				default:
					assert(0);
				}
				bit[i].val = 1;
			} else
				bit[i].val = 0;
		}
		if (buffp != buff)
			syslog(LOG_ALERT, "trigger:%s", buff);
		sleep(1);
	}
}


/*
 * Used to interface with other programs
 */
void
touch(char *s)
{
	int fd;

	if ((fd = open(s, O_CREAT | O_TRUNC | O_WRONLY, 0444)) < 0)
		syslog(LOG_ERR, "%s: %m", s);
	else
		close(fd);
}

int
main(int argc, char *argv[])
{
	int i;
	int v;
	int mode;
	FILE *f;

	daemon(0, 0);
	openlog("alarm", 0, LOG_LOCAL0);
	syslog(LOG_INFO, "starting up: pid %d", getpid());
	if ((f = fopen("/var/run/alarm.pid", "w")) == NULL)
		syslog(LOG_ERR, "/var/run/alarm.pid: %m");
	else {
		fprintf(f, "%d\n", getpid());
		fclose(f);
	}
	/* Open all ports */
	v = 0;
	for (i = 0; i < NUM_PORT; i++) {
		if ((port[i].fd = open(port[i].name, O_RDWR)) < 0)
			errexit(port[i].name);
		if (write(port[i].fd, &v, 1) < 0)
			errexit("write");
		if (close(port[i].fd) < 0)
			errexit("close");
		if ((port[i].fd = open(port[i].name, port[i].omode)) < 0)
			errexit(port[i].name);
	}

	setall(1);
	state_process();
}
