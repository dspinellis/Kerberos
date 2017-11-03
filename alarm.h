/*
 * Common definitions for all alarm modules
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

#define DELAYED	2
#define ACTIVE	1

/* The alarm board uses positive logic */
#define ON	1
#define OFF	0

/* The small sirens use positive logic */
#define SMALL_ON	ON
#define SMALL_OFF	OFF

/*
 * The main siren uses negative logic, but the relay is wired
 * to output power in its the normally closed position to avoid
 * straining its spring.
 */
#define MAIN_ON		ON
#define MAIN_OFF	OFF

#define ALL 	NULL

#define PHONE_MSG 1
#define PHONE_CMD 2

#define SENSORPATH	"/var/spool/alarm/sensor/"
#define STATUSPATH	"/var/spool/alarm/status/"
#define DISABLEPATH	"/var/spool/alarm/disable/"

#define VOICEDIR	"/var/spool/voice"
#define VMQDIR		VOICEDIR "/vmq"
#define VMAMFILE	VOICEDIR "/state/am"

#define SCRIPTDIR	"/usr/local/lib/voice"

void set_sensor_active(char *name, int val);
void zero_sensors(void);
void increment_sensors(void);
int user_disabled(int i);
void set_bit(char *name, int val);
void setall(int val);
void register_timer_event(int interval, int event);
int get_event(void);
void touch(char *s);
int vmqueue(char *cmd);
void state_process(void);
