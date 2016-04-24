LDOPT=-lwiringPi
OBJ=home.o alarm.o vmqueue.o
CFLAGS=-g
EXECUTABLES=alarmd alarm vmqueue

all: $(EXECUTABLES)

alarmd: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDOPT)

alarm.o: cmd.h alarm.h evlst.h

alarm: cmd.c cmd.h evlst.h
	$(CC) $(CFLAGS) -o $@ cmd.c

vmqueue: vmqueue.c
	$(CC) $(CFLAGS) -DCMD -o $@ vmqueue.c

home.c evlst.h: home.alr alr2c.pl
	perl alr2c.pl home.alr

clean:
	rm -f $(OBJ) alarm evlst.h home.c

install: $(EXECUTABLES)
	install alarm vmqueue alarmd /usr/local/sbin/
	install initd.sh /etc/init.d/alarm

home.dot: home.alr
	perl alr2dot.pl $? >$@

home.svg: home.dot
	dot -Tsvg -o$@ $?
