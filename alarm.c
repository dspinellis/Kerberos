/*
 * Kerberos interface program
 * Requires wiringPi API
 *
 * Kerberos DSL-configurable alarm program
 * Copyright (C) 2000-2017  Diomidis Spinellis - dds@aueb.gr
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include <fcntl.h>
#include <assert.h>
#include <stdio.h>
#include <time.h>
#include <syslog.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>
#include <wiringPi.h>

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

enum e_fun {
	SENSOR, RELAY, SPARE
};

struct s_bit {
	char *pcbname;		/* Name on the PCB */
	int physical;		/* Physical pin in Raspberry Pi 2 */
	int wpi;		/* Wiring Pi number */
	enum e_fun fun;		/* SENSOR / RELAY */
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
		if (bit[i].fun == SENSOR && bit[i].active && bit[i].val) {
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

	syslog(LOG_INFO, "set %s %s", name, val ? "on" : "off");
	for (i = 0; i < NUM_BIT; i++) {
		if (bit[i].fun != RELAY)
			continue;
		if (strcmp(bit[i].name, name) == 0) {
			digitalWrite(bit[i].wpi, val);
			return;
		}
	}
	assert(0);
}

void
setall(int val)
{
	int i;

	for (i = 0; i < NUM_BIT; i++) {
		if (bit[i].fun != RELAY)
			continue;
		digitalWrite(bit[i].wpi, val);
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
	static int ev_queue[NUM_BIT + 10];
	static int ev_count = 0;
	static int flash = 0;
	time_t now;
	char buff[512];
	char *buffp;

	for (;;) {
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

		/* Check sensors for an active one and queue events */
		buffp = buff;
		for (i = 0; i < NUM_BIT; i++) {
			if (bit[i].fun != SENSOR)
				continue;
			if (digitalRead(bit[i].wpi)) {
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

/* Setup all I/O for the alarm */
static void
setup_io(void)
{
	int i;

	wiringPiSetup();
	for (i = 0; i < NUM_BIT; i++)
		switch (bit[i].fun) {
		case SENSOR:
			pinMode(bit[i].wpi, INPUT) ;
			pullUpDnControl(bit[i].wpi, PUD_UP);
			break;
		case RELAY:
			pinMode(bit[i].wpi, RELAY) ;
			break;
		case SPARE:
			break;
		default:
			assert(0);
		}
}

/* Run the alarm system as a daemon */
static void
alarm_daemon(void)
{
	FILE *f;

	daemon(0, 0);
	openlog("alarm", 0, LOG_LOCAL0);
	syslog(LOG_INFO, "starting up: pid %d", getpid());
	if ((f = fopen("/var/run/alarmd.pid", "w")) == NULL)
		syslog(LOG_ERR, "/var/run/alarmd.pid: %m");
	else {
		fprintf(f, "%d\n", getpid());
		fclose(f);
	}

	setup_io();
	state_process();
}

static void
sensor_debug(void)
{
	int i;
	time_t now;

	setup_io();

	for (;;) {
		time(&now);
		printf("\n%s\n", ctime(&now));
		for (i = 0; i < NUM_BIT; i++) {
			if (bit[i].fun != SENSOR)
				continue;
			printf("%s %10s: %d\n", bit[i].pcbname, bit[i].name,
				digitalRead(bit[i].wpi));
		}
		sleep(1);
	}
}

static void
usage(const char *name)
{
	int i;

	fprintf(stderr, "Usage: %s [-v | -s name | -r name]\n"
			"\t-v\tShow sensor values\n"
			"\t-s name\tSet specified alarm\n"
			"\t-r name\tReset specified alarm\n"
			"\n\nAlarm names:", name
	);

	for (i = 0; i < NUM_BIT; i++)
		if (bit[i].fun == RELAY)
			fprintf(stderr, " %s", bit[i].name);
	putc('\n', stderr);

	exit(EXIT_FAILURE);
}

int
main(int argc, char *argv[])
{
	int opt;

	/* Debug options */
	opterr = 0;
	while ((opt = getopt(argc, argv, ":s:r:v")) != -1) {
		switch (opt) {
		case 'v':
			sensor_debug();
			/* NOTREACHED */
		case 's':
			if (!optarg)
				usage(argv[0]);
			printf("Set %s to 1\n", optarg);
			setup_io();
			set_bit(optarg, 1);
			exit(EXIT_SUCCESS);
		case 'r':
			if (!optarg)
				usage(argv[0]);
			printf("Set %s to 0\n", optarg);
			setup_io();
			set_bit(optarg, 0);
			exit(EXIT_SUCCESS);
		default: /* '?' */
			usage(argv[0]);
		}
	}

	alarm_daemon();
}
