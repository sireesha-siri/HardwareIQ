"""
HardwareIQ - Safe Command Execution Utility
Provides safe, restricted subprocess execution using a strict command allow-list,
shell=False, and enforced timeouts.
Compatible with Python 3.8+.
"""

import subprocess
from typing import List, Optional, Set, Tuple


# Strict allow-list of permitted binaries and allowed flags/arguments.
# Arbitrary user commands or unexpected binaries are strictly rejected.
ALLOWED_COMMANDS = {
    "lscpu": {
        "allowed_flags": {"-J", "-e", "-p", "-b", "-c", "-y"}
    },
    "lsblk": {
        "allowed_flags": {
            "-J",
            "-b",
            "-o",
            "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL",
            "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,ROTA",
            "-a",
            "-l",
            "-p",
        }
    },
    "lspci": {
        "allowed_flags": {"-v", "-nn", "-mm", "-k", "-D"}
    },
}


class CommandExecutionError(Exception):
    """Raised when a command fails or violates security policies."""
    pass


def validate_command(cmd: List[str]) -> None:
    """
    Validates that a command and its arguments are on the explicit allow-list.
    Raises CommandExecutionError if the command or any argument is not permitted.
    """
    if not isinstance(cmd, (list, tuple)) or not cmd:
        raise CommandExecutionError("Command must be a non-empty list of string arguments.")

    binary = cmd[0]
    if binary not in ALLOWED_COMMANDS:
        raise CommandExecutionError(
            f"Security Error: Command '{binary}' is not in the allowed command list: "
            f"{list(ALLOWED_COMMANDS.keys())}"
        )

    allowed_flags = ALLOWED_COMMANDS[binary]["allowed_flags"]
    for arg in cmd[1:]:
        if not isinstance(arg, str):
            raise CommandExecutionError(f"Argument '{arg}' must be a string.")
        # Reject shell operators or dangerous sequences
        if any(char in arg for char in [";", "&", "|", "`", "$", ">", "<", "\n", "\r"]):
            raise CommandExecutionError(f"Dangerous characters detected in argument: {arg}")
        if arg not in allowed_flags:
            raise CommandExecutionError(
                f"Security Error: Argument '{arg}' is not permitted for command '{binary}'."
            )


def run_safe_command(
    cmd: List[str],
    timeout: float = 5.0
) -> Tuple[bool, str, str]:
    """
    Safely executes an allow-listed command with shell=False and enforced timeout.

    Args:
        cmd: List of strings representing the binary and allowed arguments.
        timeout: Maximum execution time in seconds (default 5.0).

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str).
    """
    try:
        # Validate against explicit allow-list
        validate_command(cmd)

        # Run with shell=False, strict timeout and text output
        process = subprocess.run(
            cmd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
            check=False
        )

        success = (process.returncode == 0)
        return success, process.stdout.strip(), process.stderr.strip()

    except CommandExecutionError as ce:
        return False, "", str(ce)
    except subprocess.TimeoutExpired:
        return False, "", f"Command '{cmd[0]}' timed out after {timeout} seconds."
    except FileNotFoundError:
        return False, "", f"Command binary '{cmd[0]}' was not found on this system."
    except PermissionError:
        return False, "", f"Permission denied while trying to execute '{cmd[0]}'."
    except Exception as exc:
        return False, "", f"Unexpected error executing '{cmd[0]}': {str(exc)}"
