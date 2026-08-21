"""Machine identity and V0.1 machine-key helpers."""
from __future__ import annotations

import hashlib
import platform
import subprocess
import uuid


class MachineKeyError(RuntimeError):
    """Raised when the local machine identity cannot be read."""


def _windows_uuid() -> str:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "(Get-CimInstance Win32_ComputerSystemProduct).UUID",
    ]
    try:
        output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=5)
    except (OSError, subprocess.SubprocessError) as exc:
        raise MachineKeyError("Unable to read Windows machine UUID.") from exc
    value = output.strip().upper()
    if not value or value == "00000000-0000-0000-0000-000000000000":
        raise MachineKeyError("Windows returned an unavailable machine UUID.")
    return value


def get_machine_uuid() -> str:
    """Return a stable system identifier suitable as input to the V0.1 key."""
    if platform.system() == "Windows":
        return _windows_uuid()
    # Development fallback for non-Windows platforms. V0.1 is primarily Windows.
    value = str(uuid.getnode())
    if not value:
        raise MachineKeyError("Unable to determine machine identity.")
    return value.upper()


def get_machine_key(machine_uuid: str | None = None) -> str:
    """Derive a non-reversible V0.1 machine key from the machine UUID."""
    source = machine_uuid or get_machine_uuid()
    normalized = source.strip().upper()
    if not normalized:
        raise MachineKeyError("Machine UUID is empty.")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()
    return f"V01-{digest[:32]}"


def verify_machine_key(expected_key: str, machine_uuid: str | None = None) -> bool:
    """Constant-time comparison of an expected key with this machine's key."""
    import hmac

    actual = get_machine_key(machine_uuid)
    return hmac.compare_digest(actual, expected_key.strip().upper())
