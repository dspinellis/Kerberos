#
# Convert an alarm specification into a state transition diagram
#
# $Id: alr2dot.pl,v 1.2 2012/01/22 17:10:16 dds Exp $
#

$#ARGV == 0 || die;
open(IN, $fname = $ARGV[0]) || die "Unable to read from $fname: $!\n";

print "digraph state {
	size=\"8,11.5\";
	rotate=90;
	node [height=0.3,fontname=\"Helvetica\",fontsize=8,shape=record,style=rounded];
	_start [shape=circle,style=filled,label=\"START\",height=0.5,fixedsize=true];
	edge [fontname=\"Helvetica\", fontsize=8];
";
while (<IN>) {
	chop;
	s/^#.*//;
	next if (/^$/);
	if (/^(\w+):$/) {
		# State begin
		$state = $1;
		undef $cmd;
		undef $indefault;
	} elsif (/^\%\{$/) {
		while (<IN>) {
			last if (/^\%\}/);
		}
	} elsif (/^\*:$/) {
		$indefault = 1;
	} elsif (/^\%i (\w+)/) {
		$trans .= "\t_start -> $1;\n";
	} elsif (/^\s*\|([=><]\d+)?\s+(.*)/) {
		# Command before state
		$count = $1;
		$command = $2;
		$command =~ s/ClearCounter\((\w+)\)/state_count[ST_$1] = 0/;
		$command =~ s/call\s+(\w+)/proc_ST_$1()/;
		if ($count ne '') {
			$cmd .= "[$count] $command\\n";
		} else {
			$cmd .= "$command\\n";
		}
	} elsif (/^\s*(\w+)?\s*\>\s*(\w+)/) {
		# State transition
		$event = $1;
		$newstate = $2;
		if ($indefault) {
			$fromstate = "tmp" . $tmp++;
			print "\t$fromstate [shape=plaintext,label=\"\"];\n";
		} else {
			$fromstate = $state;
		}
		$trans .= "\t$fromstate -> $newstate [label=\"$event\"];\n";
	} elsif (/\s*\;\s*$/) {
		# End of state spec
		$cmd =~ s/\"/\\"/g;
		#print "\t$state [label=\"$cmd\"];\n" unless ($indefault);
		print "\t$state [label=\"$state\"];\n" unless ($indefault);
	} else {
		print STDERR "$.: syntax error [$_]\n";
		$err++;
	}
}
print "$trans
}
";



exit($err ? 1 : 0);
