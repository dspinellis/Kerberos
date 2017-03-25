/*
 * Home alarm program
 * Voice-mail interface
 *
 * (C) Copyright 2001 Diomidis Spinellis.  All rights reserved.
 *
 * $Id: vmqueue.c,v 1.4 2001/11/22 15:00:54 dds Exp $
 *
 */

#include <unistd.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <syslog.h>
#include <string.h>

#include "alarm.h"

/*
 * Queue ;-separeted series of cmd for execution by vmd
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

	for (s = strtok(cmdcopy, ";"); s; s = strtok(NULL, ";"))
		fprintf(f, "vm shell -l ttyUSB0 -S /usr/bin/perl " SCRIPTDIR "/%s ||\n", s);
	fprintf(f, "true\n");
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
	if (argc != 2) {
		fprintf(stderr, "usage: %s command\n", argv[0]);
		return (1);
	}
	return vmqueue(argv[1]);
}
#endif
