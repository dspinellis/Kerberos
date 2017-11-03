#!/usr/bin/env perl
#
# Convert an alarm specification into a state transition diagram
#
# Kerberos DSL-configurable alarm program
# Copyright (C) 2000-2017  Diomidis Spinellis - dds@aueb.gr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
