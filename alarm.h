#define DELAYED	2
#define ACTIVE	1

#define ON	1
#define OFF	0

/* The small siren uses positive logic */
#define SMALL_ON	ON
#define SMALL_OFF	OFF

/* The main siren uses negative logic */
#define MAIN_ON		OFF
#define MAIN_OFF	ON

#define ALL 	NULL

#define PHONE_MSG 1
#define PHONE_CMD 2

#define SENSORPATH	"/var/spool/alarm/sensor/"
#define STATUSPATH	"/var/spool/alarm/status/"
#define DISABLEPATH	"/var/spool/alarm/disable/"

#define VOICEDIR	"/var/spool/voice"
#define VMQDIR		VOICEDIR "/vmq"

#define SCRIPTDIR	"/usr/home/dds/voice"
