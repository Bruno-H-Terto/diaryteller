"""Domain errors shared by models and services."""

from __future__ import annotations


class DeviceConflict(Exception):
    """The random device id already belongs to another account."""
