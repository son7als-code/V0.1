from __future__ import annotations

import pytest

from app.core.machine import MachineKeyError, get_machine_key, verify_machine_key


def test_machine_key_is_deterministic():
    value = "36C78E6F-52A6-742A-CBD8-D48D64B7471C"
    assert get_machine_key(value) == get_machine_key(value.lower())
    assert get_machine_key(value) == "V01-43028C5E3BB5176391B7072A36D39F1F"


def test_machine_key_does_not_expose_uuid():
    value = "36C78E6F-52A6-742A-CBD8-D48D64B7471C"
    assert value not in get_machine_key(value)


def test_verify_machine_key():
    value = "36C78E6F-52A6-742A-CBD8-D48D64B7471C"
    key = get_machine_key(value)
    assert verify_machine_key(key, value)
    assert not verify_machine_key(key + "X", value)


def test_empty_machine_uuid_rejected():
    with pytest.raises(MachineKeyError):
        get_machine_key("   ")
