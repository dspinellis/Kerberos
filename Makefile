#
# Alarm system's build file
# The following targets have their usual meaning: all install clean
# In addition, make $SPEC.svg will create a state machine diagram
# of the alarm specification.
#

# Configuration starts here
# Specify here the alarm specification
# This comprises:
# a $SPEC.alr file with the state transition rules and the
# a $SPEC.h file with the port mappings
SPEC=home
# Configuration starts here

LDOPT=-lwiringPi
OBJ=$(SPEC).o alarm.o vmqueue.o
CFLAGS=-g
EXECUTABLES=alarmd alarm vmqueue

.SUFFIXES:.dot .svg .alr

%.dot: %.alr
	perl alr2dot.pl $? >$@

%.svg: %.dot
	dot -Tsvg -o$@ $?

all: $(EXECUTABLES)

alarmd: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDOPT)

alarm.o: cmd.h cmd-def.h alarm.h evlst.h alarm-spec.h
	$(CC) $(CFLAGS) -o $@ alarm.c

alarm-spec.h: $(SPEC)-io.h
	cp $? $@

cmd-def.h: $(SPEC)-cmd.h
	cp $? $@

alarm: cmd.c cmd.h cmd-def.h evlst.h
	$(CC) $(CFLAGS) -o $@ cmd.c

vmqueue: vmqueue.c
	$(CC) $(CFLAGS) -DCMD -o $@ vmqueue.c

$(SPEC).c evlst.h: $(SPEC).alr alr2c.pl
	perl alr2c.pl $(SPEC).alr

clean:
	rm -f $(OBJ) alarm alarmd vmqueue evlst.h $(SPEC).c

install: $(EXECUTABLES)
	install alarm vmqueue alarmd /usr/local/sbin/
	install alarm-sms.sh /usr/local/sbin/alarm-sms
	install initd.sh /etc/init.d/alarm
	systemctl daemon-reload
