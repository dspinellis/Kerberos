/*
 * Command-line and interactive alarm interface
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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "evlst.h"
#include "cmd.h"

static void
runcmd(int i)
{
	int fd;

	if ((fd = open(cmd[i].fname, O_CREAT | O_TRUNC | O_WRONLY, 0444)) < 0) {
		perror(cmd[i].fname);
		exit(1);
	}
	close(fd);
}

static void
help()
{
	int i;

	printf("Valid commands are:\n");
	printf("x: eXit this command line interface\n");
	for (i = 0; i < NUM_CMD; i++)
		printf("%c: %s\n", cmd[i].key, cmd[i].name);
	printf("Commands can be given as a character in command mode\n"
		"or preceded by a dash as a command line argument\n");
}

int
main(int argc, char *argv[])
{
	char buff[10];
	int i;

	if (argc == 2) {
		/* Command-line interface */
		for (i = 0; i < NUM_CMD; i++)
			if (argv[1][0] == '-' && cmd[i].key == argv[1][1]) {
				runcmd(i);
				exit(0);
			}
		help();
		exit(1);
	} else
		/* Interactive shell */
		help();
		for (;;) {
			printf("Enter remote command:");
			fgets(buff, sizeof(buff), stdin);
			if (*buff == 'x')
				exit(0);
			for (i = 0; i < NUM_CMD; i++)
				if (*buff == cmd[i].key) {
					printf("%s\n", cmd[i].name);
					runcmd(i);
					break;
				}
			if (i == NUM_CMD)
				help();
		}
}
