#
# Convert an alarm specification into C state machine
#
# $Id: alr2c.pl,v 1.1 2001/01/27 11:03:31 dds Exp $
#

$#ARGV == 0 || die;
open(IN, $fname = $ARGV[0]) || die "Unable to read from $fname: $!\n";
$basename = $fname;
$prologue = "/*
 *
 * Automatically generated file.  Do not modify.
 * Modify $fname instead.
 */
";
$basename =~ s/\.[^.]*$//;
open(OUT, ">$basename.c") || die "Unable to write to $basename.c: $!\n";
print OUT $prologue;

open(EV, ">evlst.h") || die;
print EV $prologue;

while (<IN>) {
	chop;
	s/#.*//;
	next if (/^$/);
	if (/^(\w+):$/) {
		# State begin
		$state = "ST_$1";
		$states{$state} = 1;
		undef $cmd;
		undef $trans;
		undef $indefault;
	} elsif (/^\%\{$/) {
		while (<IN>) {
			last if (/^\%\}/);
			print OUT;
		}
	} elsif (/^\*:$/) {
		$indefault = 1;
	} elsif (/^\%i (\w+)/) {
		# Initial state specification
		$istate = $1;
	} elsif (/^\s*\|([=><]\d+)?\s+(.*)/) {
		# Command before state
		$count = $1;
		$command = $2;
		$command =~ s/ClearCounter\((\w+)\)/state_count[ST_$1] = 0/;
		$count =~ s/\=/==/;
		if ($count ne '') {
			$cmd .= "\tif(state_count[$state] $count) $command;\n";
		} else {
			$cmd .= "\t$command;\n";
		}
	} elsif (/^\s*(\w+)?\s*\>\s*(\w+)/) {
		# State transition
		$event = $1;
		$newstate = "ST_$2";
		if ($event =~ m/^(\d+)s$/) {
			$event = "EV_TIMER_$1";
			$cmd .= "\tregister_timer_event($1, $event);\n";
		} elsif ($event ne '') {
			$event = "EV_$event";
		}
		if ($event ne '') {
			$events{$event} = 1;
			$x = "\tcase $event: state = $newstate; break;\n";
			if ($indefault) {
				$deftrans .= $x;
			} else {
				$trans .= $x;
			}
		} else {
			$cmd .= "\tstate = $newstate;\n";
		}
	} elsif (/\s*\;\s*$/) {
		# End of state spec
		$cbody .= "
static void
proc_$state(void)
{
	state_count[$state]++;
$cmd\n" unless($indefault);
		if ($trans) {
			$cbody .= "
	switch(get_event()) {
$deftrans
$trans
	}
";
		}
	$cbody .= "}\n\n" unless($indefault);
	} else {
		print STDERR "$.: syntax error [$_]\n";
	}
}

$chead .= "
static enum e_states {
";

$cbody .= '
void
state_process(void)
{
	for (;;)
		switch (state) {
';


for $s (keys %states) {
	$chead .= "\t$s,\n";
	$cbody .= "\t\tcase $s: proc_$s(); break;\n";
}

$cbody .= '
		}
}
';

$chead .= "
	NUM_STATES
} state = ST_$istate;

static int state_count[NUM_STATES];
";

print OUT $chead;
print OUT $cbody;

print EV "
enum e_evlst {
";
for $e (keys %events) {
	print EV "\t$e,\n";
}
print EV "\tNUM_EVLST\n};\n";
close(EV);
