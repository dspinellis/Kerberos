/*
 * Home alarm interface program
 * Requires the pbio driver
 *
 * (C) Copyright 2000, 2001 Diomidis Spinellis.  All rights reserved.
 *
 * $Id: alarm.c,v 1.12 2001/03/18 22:17:53 dds Exp $
 *
 */

#include "/sys/sys/pbioio.h"
#include <fcntl.h>
#include <assert.h>
#include <stdio.h>
#include <errno.h>
#include <time.h>
#include <syslog.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>

void
errexit(char *s)
{
	fprintf(stderr, "%s: %s\n", s, strerror(errno));
	exit(1);
}

enum e_port {
	PA, PB, PCH, PCL
};

enum e_fun {
	SENSE, OUTPUT
};

#define NUM_BIT (sizeof(bit) / sizeof(struct s_bit))

struct s_port {
	char *name;
	int omode;
	int fd;
} port[] = {
	{"/dev/pbio0a", O_RDWR},
	{"/dev/pbio0b", O_RDWR},
	{"/dev/pbio0ch", O_RDONLY},
	{"/dev/pbio0cl", O_RDONLY},
};

#define NUM_PORT (sizeof(port) / sizeof(struct s_port))


int
main(int argc, char *argv[])
{
	int i;
	int v;
	int mode;
	FILE *f;
	int j;
	int data;
	unsigned char buff[1];

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
		/* hz = 100 => 1 sec */
		data = 100;
		if (ioctl(port[i].fd, PBIO_SETIPACE, &data) < 0)
			errexit(port[i].name);
		data = 0;
		if (ioctl(port[i].fd, PBIO_GETIPACE, &data) < 0)
			errexit(port[i].name);
		printf("%s ipace %d\n", port[i].name, data);
		data = 0;
		if (ioctl(port[i].fd, PBIO_SETDIFF, &data) < 0)
			errexit(port[i].name);
		data = 0;
		if (ioctl(port[i].fd, PBIO_GETDIFF, &data) < 0)
			errexit(port[i].name);
		printf("%s diff %d\n", port[i].name, data);
	}

	for (j = 0; j < 5; j++) {
		for (i = 0; i < NUM_PORT; i++) {

			if (read(port[i].fd, buff, sizeof(buff)) != sizeof(buff))
				errexit(port[i].name);
			printf("%12s: %02x  ", port[i].name, buff[0]);
		}
		putchar('\n');
	}
	data = 1;
	if (ioctl(port[1].fd, PBIO_SETDIFF, &data) < 0)
		errexit(port[1].name);
	data = 10;
	if (ioctl(port[1].fd, PBIO_SETIPACE, &data) < 0)
		errexit(port[1].name);
	for (;;) {
		if (read(port[1].fd, buff, 1) != 1)
			errexit(port[1].name);
		printf("Read %02x\n", buff[0]);
	}
}
