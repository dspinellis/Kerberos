/*
 * Home alarm program
 * Voice-mail interface
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

#include <sys/stat.h>

#include <ctype.h>
#include <unistd.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <syslog.h>
#include <string.h>

#include "alarm.h"

/*
 * Queue ;-separated parts of cmd for execution by vmd
 * The first part to succeed will successfully terminate all ;-reparated
 * commands.
 * Return 0 if ok, -1 on error
 * All errors get logged via syslog(3)
 */
int
vmqueue(char *cmd)
{
	char tmptemplate[] = VMQDIR "/tmp.XXXXXX";
	char *tmpfname;
	FILE *f;
	char newfname[1024];
	struct tm *t;
	time_t now;
	char cmdcopy[1024];
	char *s;

	if ((tmpfname = mktemp(tmptemplate)) == NULL) {
		syslog(LOG_ERR, "%s: %m", tmptemplate);
		return (-1);
	}
	if ((f = fopen(tmpfname, "w")) == NULL) {
		syslog(LOG_ERR, "open(%s): %m", tmpfname);
		return (-1);
	}
	strcpy(cmdcopy, cmd);

	for (s = strtok(cmdcopy, ";"); s; s = strtok(NULL, ";")) {
		while (isspace(*s))
			s++;
		fprintf(f, "vm shell -v -x 1 -l modem -S /usr/bin/perl " SCRIPTDIR "/%s && exit 0\n", s);
	}
	if (fclose(f) != 0) {
		syslog(LOG_ERR, "close(%s): %m", tmpfname);
		return (-1);
	}
	if (chmod(tmpfname, 0755) != 0) {
		syslog(LOG_ERR, "chmod(%s): %m", tmpfname);
		return (-1);
	}
	time(&now);
	t = localtime(&now);
	sprintf(newfname, VMQDIR "/vm.%04d.%02d.%02d.%02d.%02d.%02d",
		t->tm_year + 1900, t->tm_mon + 1,
		t->tm_mday, t->tm_hour, t->tm_min, t->tm_sec);
	if (rename(tmpfname, newfname) != 0) {
		syslog(LOG_ERR, "rename(%s, %s): %m", tmpfname, newfname);
		return (-1);
	}
	return (0);
}

#ifdef CMD
int
main(int argc, char *argv[])
{
	int ret;

	if (argc != 2) {
		fprintf(stderr, "usage: %s command\n", argv[0]);
		return (1);
	}
	ret = vmqueue(argv[1]);
	if (ret != 0) {
		fprintf(stderr, "%s: failed. Check error log\n", argv[0]);
		return 1;
	} else
		return 0;
}
#endif
