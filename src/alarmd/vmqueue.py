import os
import sys
import tempfile
import time
from syslog import syslog, LOG_ERR

# Constants
VOICEDIR = "/var/spool/voice"
VMQDIR = VOICEDIR + "/vmq"
SCRIPTDIR = "/usr/local/lib/voice"


def vmqueue(cmd):
    """
    Queue ;-separated parts of cmd for execution by vmd.
    The first part to succeed will successfully terminate all ;-separated commands.
    Returns 0 if ok, -1 on error.
    Errors are logged via Python's logging module.

    Args:
        cmd (str): Command string with ;-separated parts.

    Returns:
        int: 0 if successful, -1 if an error occurred.
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, dir=VMQDIR, prefix="tmp.", mode="w"
        ) as temp_file:
            tmpfname = temp_file.name

            # Write commands to the temporary file
            cmd_parts = cmd.split(";")
            for part in cmd_parts:
                part = part.strip()
                temp_file.write(
                    f"vm shell -v -x 1 -l modem -S /usr/bin/perl {SCRIPTDIR}/{part} && exit 0\n"
                )

        # Make the temporary file executable
        os.chmod(tmpfname, 0o755)

        # Generate a new filename
        now = time.localtime()
        newfname = os.path.join(
            VMQDIR,
            f"vm.{now.tm_year:04d}.{now.tm_mon:02d}.{now.tm_mday:02d}.{now.tm_hour:02d}.{now.tm_min:02d}.{now.tm_sec:02d}",
        )

        # Rename the temporary file to the new filename
        os.rename(tmpfname, newfname)

        return 0

    except Exception as e:
        syslog(LOG_ERR, f"Error: {e}")
        return -1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} command", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]
    ret = vmqueue(command)

    if ret != 0:
        print(f"{sys.argv[0]}: failed. Check error log", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)
