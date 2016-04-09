LDOPT=-lwiringPi
OBJ=home.o alarm.o vmqueue.o
CFLAGS=-g

all: alarm cmd vmqueue

alarm: $(OBJ)
	$(CC) $(CFLAGS) -o alarm $(OBJ) $(LDOPT)

alarm.o: cmd.h alarm.h evlst.h

cmd: cmd.c cmd.h evlst.h
	$(CC) $(CFLAGS) -o cmd cmd.c

vmqueue: vmqueue.c
	$(CC) $(CFLAGS) -DCMD -o vmqueue vmqueue.c

home.c evlst.h: home.alr alr2c.pl
	perl alr2c.pl home.alr

clean:
	rm -f $(OBJ) alarm evlst.h home.c

home.dot: home.alr
	perl alr2dot.pl $? >$@

home.svg: home.dot
	dot -Tsvg -o$@ $?
