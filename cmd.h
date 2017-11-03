/*
 * Command definitions template
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

#define CMDPATH "/var/spool/alarm/cmd/"

/* Macro for creating struct entries */
#define CMD(flag, help, symbol) \
	{ flag, help, CMDPATH # symbol, EV_Cmd ## symbol },

static struct s_cmd {
	char key;	/* Key press */
	char *name;	/* Human readable name */
	char *fname;	/* File name to trigger the command */
	int event;	/* Event to generate */
} cmd[] =
{
#include "cmd-def.h"
};

#define NUM_CMD (sizeof(cmd) / sizeof(struct s_cmd))
