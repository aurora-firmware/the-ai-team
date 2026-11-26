"""Shared pytest fixtures for the CLI tests."""

from __future__ import annotations

import fcntl
import threading

import pytest

from ai_team.core import lock


class _ContentionSignallingFcntl:
    """Stand-in for ``fcntl`` that reports when ``flock`` finds the lock held."""

    def __init__(self, contended: threading.Event) -> None:
        self._contended = contended

    def __getattr__(self, name: str):
        return getattr(fcntl, name)

    def flock(self, fd: int, operation: int) -> None:
        try:
            fcntl.flock(fd, operation)
        except BlockingIOError:
            self._contended.set()
            raise


@pytest.fixture
def lock_contended(monkeypatch: pytest.MonkeyPatch) -> threading.Event:
    """Event set once a caller of ``ai_team.core.lock`` is refused a held lock.

    Only the ``fcntl`` name inside ``ai_team.core.lock`` is replaced, so the
    real lock is still taken and the caller keeps polling for it.
    """
    contended = threading.Event()
    monkeypatch.setattr(lock, "fcntl", _ContentionSignallingFcntl(contended))
    return contended
