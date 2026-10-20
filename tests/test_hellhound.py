"""Tests for the root HellHound.py educational tool.

Pins the owner's design directive: NO mid-run stopping. Once a run has
been consented to and started, it completes its announced scope —
Ctrl+C during the run is announced and disregarded (scan, processing,
and directory cleanup alike). Ctrl+C is honored only BEFORE a run
starts, at the prompts in main(), where aborting is the consent gate
working as designed.

All tests run against synthetic trees in pytest tmp dirs only.
"""

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("cryptography")  # HellHound.py's Fernet dependency

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import HellHound  # noqa: E402


@pytest.fixture(autouse=True)
def reset_stats():
    """HellHound.stats is module-global; isolate every test from it."""
    snapshot = dict(HellHound.stats)
    HellHound.stats.update(
        {
            "total_files_deleted": 0,
            "total_dirs_deleted": 0,
            "total_encrypted": 0,
            "total_size_deleted": 0,
            "total_size_encrypted": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }
    )
    HellHound.stats.pop("execution_time", None)
    yield
    HellHound.stats.clear()
    HellHound.stats.update(snapshot)


def _make_tree(root: Path, count: int = 60) -> Path:
    """A synthetic target tree: half the files nested in a subdir."""
    target = root / "target"
    (target / "sub").mkdir(parents=True)
    for i in range(count // 2):
        (target / f"file_{i}.txt").write_text("x")
    for i in range(count - count // 2):
        (target / "sub" / f"nested_{i}.txt").write_text("x")
    return target


def _files_left(target: Path) -> int:
    return sum(1 for p in target.rglob("*") if p.is_file())


def _interrupt_first_wait(monkeypatch):
    """Raise KeyboardInterrupt once, where a real Ctrl+C lands: the
    main thread blocked in wait() during processing."""
    real_wait = HellHound.wait
    state = {"raised": False}

    def flaky(fs, **kwargs):
        if not state["raised"]:
            state["raised"] = True
            raise KeyboardInterrupt
        return real_wait(fs, **kwargs)

    monkeypatch.setattr(HellHound, "wait", flaky)


def _interrupt_walk_call(monkeypatch, call_number: int):
    """Raise KeyboardInterrupt on the Nth os.walk call (1 = scan,
    2 = the directory-cleanup walk)."""
    real_walk = os.walk
    state = {"calls": 0}

    def flaky(*args, **kwargs):
        state["calls"] += 1
        if state["calls"] == call_number:
            raise KeyboardInterrupt
        return real_walk(*args, **kwargs)

    monkeypatch.setattr(os, "walk", flaky)


# ---------------------------------------------------------------------------
# Baseline: a run completes its announced scope
# ---------------------------------------------------------------------------


def test_run_completes_announced_scope(tmp_path):
    target = _make_tree(tmp_path)
    deleted, dirs_deleted = HellHound.delete_directory_contents_threaded(str(target))
    assert deleted == 60
    assert dirs_deleted == 1  # the emptied "sub" directory
    assert _files_left(target) == 0


# ---------------------------------------------------------------------------
# Ctrl+C during a run: announced, disregarded, scope still completes
# ---------------------------------------------------------------------------


def test_ctrl_c_during_processing_does_not_truncate_scope(tmp_path, monkeypatch, capsys):
    target = _make_tree(tmp_path)
    _interrupt_first_wait(monkeypatch)
    deleted, _ = HellHound.delete_directory_contents_threaded(str(target))
    assert deleted == 60
    assert _files_left(target) == 0
    out = capsys.readouterr().out
    # The keypress is announced, never silent — and the old stop
    # announcement is gone.
    assert "does not stop mid-run" in out
    assert "Stop requested" not in out
    assert "will NOT be processed" not in out


def test_ctrl_c_during_scan_does_not_truncate_scope(tmp_path, monkeypatch, capsys):
    target = _make_tree(tmp_path)
    _interrupt_walk_call(monkeypatch, 1)
    deleted, _ = HellHound.delete_directory_contents_threaded(str(target))
    assert deleted == 60
    assert _files_left(target) == 0
    assert "does not stop mid-run" in capsys.readouterr().out


def test_ctrl_c_during_cleanup_does_not_truncate_scope(tmp_path, monkeypatch, capsys):
    target = _make_tree(tmp_path)
    _interrupt_walk_call(monkeypatch, 2)
    deleted, dirs_deleted = HellHound.delete_directory_contents_threaded(str(target))
    assert deleted == 60
    assert dirs_deleted == 1
    assert _files_left(target) == 0
    assert "does not stop mid-run" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Ctrl+C before a run starts: the consent gate still aborts cleanly
# ---------------------------------------------------------------------------


def test_ctrl_c_at_prompt_aborts_before_anything_is_touched(tmp_path, monkeypatch):
    target = _make_tree(tmp_path)
    monkeypatch.chdir(tmp_path)  # the JSON report lands in the tmp CWD
    monkeypatch.setattr(HellHound, "display_hellhound_message", lambda: None)
    monkeypatch.setattr(HellHound, "get_target_paths", lambda: [str(target)])

    def raising_input(_prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raising_input)
    with pytest.raises(SystemExit) as excinfo:
        HellHound.main()
    assert excinfo.value.code == 0
    # Nothing was touched, and the abort is still reported as before.
    assert _files_left(target) == 60
    assert (tmp_path / "hellhound_report.json").exists()
