/*
 * Command definitions
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

/*
 * For each command specify the following.
 * - The command line interface flag (or interactive shortcut letter)
 * - The command's human-readable description
 * - The symbol used in the state machine specification file
 */

/* Flag 	Help			Event name */
CMD('d',	"Day arm",		DayArm)
CMD('q',	"Quit",			Quit)
CMD('e',	"lEave",		Leave)
CMD('i',	"dIsarm",		Disarm)
