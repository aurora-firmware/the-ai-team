"""
Tests for B-014: ai_team.core.lock — project-local mutual exclusion for
concurrent artifact ID allocation.

Cycle 1 scope:
  - ``allocation_lock`` serializes two real threads racing for the same lock.
  - ``allocation_lock`` releases on normal exit and on exception.
  - ``allocation_lock`` raises ``LockTimeout`` after a bounded wait instead of
    hanging forever when another holder does not release in time.
  - ``create_artifact_with_lock`` prevents the diagnosed scan-then-write race:
    two concurrent callers of "scan for next id, then write" never observe
    the same "next id" once wrapped in the lock.

All coordination below uses ``threading.Event``/``threading.Barrier`` with a
bounded ``timeout=`` as a hang safety net only — never ``time.sleep`` to
control ordering between threads.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from ai_team.core.lock import LockTimeout, allocation_lock, create_artifact_with_lock
from ai_team.core.models import Task

# ---------------------------------------------------------------------------
# allocation_lock: mutual exclusion, release-on-exit, release-on-exception,
# bounded timeout.
# ---------------------------------------------------------------------------


def test_allocation_lock_serializes_two_threads_racing_for_the_same_lock(
    tmp_path, lock_contended
):
    """A second thread's critical section never overlaps the first's."""
    project_dir = tmp_path / "ai-team"
    project_dir.mkdir()

    order: list[str] = []
    order_lock = threading.Lock()
    first_holder_entered = threading.Event()
    release_first_holder = threading.Event()

    def first_holder() -> None:
        with allocation_lock(project_dir):
            with order_lock:
                order.append("first-enter")
            first_holder_entered.set()
            # Bounded wait is a hang safety net only; the assertions below
            # prove mutual exclusion by call ordering, not by timing.
            assert release_first_holder.wait(timeout=5), "never released"
            with order_lock:
                order.append("first-exit")

    def second_holder() -> None:
        assert first_holder_entered.wait(timeout=5), "first holder never entered"
        with allocation_lock(project_dir):
            with order_lock:
                order.append("second-enter")

    t1 = threading.Thread(target=first_holder)
    t2 = threading.Thread(target=second_holder)
    t1.start()
    assert first_holder_entered.wait(timeout=5)
    t2.start()

    # Wait until the second thread has been refused the lock the first still
    # holds; the timeout only guards against a hang.
    assert lock_contended.wait(timeout=5), "second thread never reached the held lock"
    assert "second-enter" not in order, "second thread entered while the lock was held"

    release_first_holder.set()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive()
    assert not t2.is_alive()

    assert order == ["first-enter", "first-exit", "second-enter"]


def test_allocation_lock_releases_after_a_normal_exit_so_a_later_caller_can_acquire(
    tmp_path,
):
    """The lock is available again once a completed ``with`` block exits."""
    project_dir = tmp_path / "ai-team"
    project_dir.mkdir()

    with allocation_lock(project_dir):
        pass

    acquired = threading.Event()

    def later_caller() -> None:
        with allocation_lock(project_dir, timeout=2):
            acquired.set()

    t = threading.Thread(target=later_caller)
    t.start()
    t.join(timeout=5)
    assert acquired.is_set()


def test_allocation_lock_releases_even_when_the_block_raises(tmp_path):
    """A crashing holder still releases the lock; no stale lock is left behind."""
    project_dir = tmp_path / "ai-team"
    project_dir.mkdir()

    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        with allocation_lock(project_dir):
            raise Boom("simulated crash inside the critical section")

    # A fresh acquisition must not block, proving the lock was released.
    with allocation_lock(project_dir, timeout=1):
        pass


def test_allocation_lock_raises_lock_timeout_when_already_held(tmp_path):
    """Acquisition gives up after the bounded timeout instead of hanging forever."""
    project_dir = tmp_path / "ai-team"
    project_dir.mkdir()

    holder_entered = threading.Event()
    release_holder = threading.Event()

    def holder() -> None:
        with allocation_lock(project_dir):
            holder_entered.set()
            release_holder.wait(timeout=5)

    t = threading.Thread(target=holder)
    t.start()
    assert holder_entered.wait(timeout=5)

    try:
        with pytest.raises(LockTimeout):
            with allocation_lock(project_dir, timeout=0.2):
                pass  # pragma: no cover - must never be entered
    finally:
        release_holder.set()
        t.join(timeout=5)


# ---------------------------------------------------------------------------
# create_artifact_with_lock: the shared "scan -> build -> write" helper that
# task/bug/spec `new` commands call.
# ---------------------------------------------------------------------------


def _build_task(dest_dir: Path, title: str):
    def build(task_id: str) -> tuple[Path, Task, str]:
        dest = dest_dir / f"{task_id}-{title.lower()}.md"
        model = Task(
            id=task_id,
            title=title,
            status="pending",
            priority="medium",
            assigned_role="unassigned",
            created="2026-08-06",
            spec=None,
        )
        return dest, model, "Body.\n"

    return build


def test_create_artifact_with_lock_prevents_interleaved_scans_across_two_threads(
    tmp_path, lock_contended
):
    """The lock serializes 'scan for next id' + 'write' so two callers never collide.

    Mirrors B-014's diagnosed race directly: without the lock, thread one's
    directory scan and thread two's directory scan could interleave before
    either writes, so both compute the same "next id". Delaying thread one's
    scan (via a shared ``Event``, never ``time.sleep``) widens that race
    window deterministically; the fix must still stop thread two's scan from
    starting until thread one's entire allocate+write critical section has
    completed.
    """
    project_dir = tmp_path / "ai-team"
    dest_dir = project_dir / "tasks" / "pending"
    dest_dir.mkdir(parents=True)

    scan_started = threading.Event()
    release_scan = threading.Event()
    call_order: list[str] = []
    order_lock = threading.Lock()
    calls = {"count": 0}

    def allocate_id() -> str:
        with order_lock:
            calls["count"] += 1
            this_call = calls["count"]
            call_order.append(f"scan-start-{this_call}")
        if this_call == 1:
            scan_started.set()
            assert release_scan.wait(timeout=5), "scan was never released"
        existing = sorted(dest_dir.glob("T-*.md"))
        next_number = len(existing) + 1
        with order_lock:
            call_order.append(f"scan-end-{this_call}")
        return f"T-{next_number:03d}"

    build = _build_task(dest_dir, "Task")

    results: dict[str, tuple[str, Path]] = {}
    errors: list[BaseException] = []

    def worker(name: str) -> None:
        try:
            results[name] = create_artifact_with_lock(
                project_dir, allocate_id=allocate_id, build=build
            )
        except BaseException as exc:  # noqa: BLE001 - surfaced via `errors`
            errors.append(exc)

    t1 = threading.Thread(target=worker, args=("first",))
    t1.start()
    assert scan_started.wait(timeout=5)

    t2 = threading.Thread(target=worker, args=("second",))
    t2.start()

    # Wait until the second caller has been refused the lock the first still
    # holds mid-scan; the timeout only guards against a hang.
    assert lock_contended.wait(timeout=5), "second caller never reached the held lock"
    assert calls["count"] == 1, "second caller must not start its scan yet"

    release_scan.set()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert not t1.is_alive()
    assert not t2.is_alive()

    assert errors == []
    assert call_order == ["scan-start-1", "scan-end-1", "scan-start-2", "scan-end-2"]

    ids = {name: outcome[0] for name, outcome in results.items()}
    assert len(set(ids.values())) == 2
    for _, dest in results.values():
        assert dest.exists()


def test_create_artifact_with_lock_propagates_artifact_exists_without_leaking_the_lock(
    tmp_path,
):
    """When ``write_artifact`` refuses to overwrite, the lock is still released."""
    from ai_team.core.fs import ArtifactExists

    project_dir = tmp_path / "ai-team"
    dest_dir = project_dir / "tasks" / "pending"
    dest_dir.mkdir(parents=True)

    existing = dest_dir / "T-001-task.md"
    existing.write_text("existing bytes\n", encoding="utf-8")

    build = _build_task(dest_dir, "Task")

    with pytest.raises(ArtifactExists):
        create_artifact_with_lock(project_dir, allocate_id=lambda: "T-001", build=build)

    assert existing.read_text(encoding="utf-8") == "existing bytes\n"

    # The lock must have been released despite the raised exception.
    with allocation_lock(project_dir, timeout=1):
        pass
