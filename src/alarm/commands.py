# List of supported commands

from .command import Command

commands = [
#           Flag Event name                 # Help
    Command("d", "DayArm",                   "Day arm"),
    Command("q", "Quit",                     "Quit"),
    Command("e", "Leave",                    "lEave"),
    Command("i", "Disarm",                   "dIsarm"),
]
