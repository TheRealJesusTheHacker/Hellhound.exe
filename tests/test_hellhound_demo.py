"""Headless smoke tests for the HELLHOUND visual demo.

Runs with QT_QPA_PLATFORM=offscreen so no display is needed. Verifies the
virtual filesystem is deterministic and in-memory only, the demo builds its
full UI, the kill chain runs to completion on virtual files, and the
theatrical "no escape" close refusal still works (it is intentional).
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "visual-demo"))
import hellhound_demo as demo  # noqa: E402

from PyQt5.QtTest import QSignalSpy, QTest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


# ---------------------------------------------------------------------------
# Virtual filesystem -- deterministic, in-memory, 256 targets
# ---------------------------------------------------------------------------


def test_virtualfs_has_256_targets():
    vfs = demo.VirtualFS()
    assert len(vfs.targets) == 256


def test_virtualfs_is_deterministic():
    first = [(t.dirpath, t.name, t.size_kb) for t in demo.VirtualFS().targets]
    second = [(t.dirpath, t.name, t.size_kb) for t in demo.VirtualFS().targets]
    assert first == second
    assert first  # non-empty


def test_virtualfs_totals_are_positive():
    vfs = demo.VirtualFS()
    assert vfs.total_kb > 0
    assert all(12 <= t.size_kb <= 8192 for t in vfs.targets)


def test_targets_cover_expected_directories():
    dirs = {t.dirpath for t in demo.VirtualFS().targets}
    assert "C:\\Windows\\System32" in dirs
    assert "C:\\Users\\Victim\\Documents" in dirs
    assert "D:\\Backups" in dirs


def test_educational_phases_have_content():
    assert len(demo.PHASES) == 5
    for name, seeing, defense in demo.PHASES:
        assert name and seeing and defense


# ---------------------------------------------------------------------------
# UI builds offscreen
# ---------------------------------------------------------------------------


def test_main_window_builds(app):
    win = demo.MainWindow()
    try:
        assert len(win._tree_items) == 256
        assert len(win.phase_pills) == 5
        assert "SIMULATION" in win.sim_badge.text()
        assert win.stat_deleted.text() == "0"
        assert win.launch_btn.isEnabled()
        assert win.reset_btn.isEnabled()
    finally:
        win.close()
        win.deleteLater()


def test_close_allowed_when_idle(app):
    win = demo.MainWindow()
    try:
        assert win.close() is True  # closeEvent accepts when no engine runs
    finally:
        win.deleteLater()


# ---------------------------------------------------------------------------
# No-escape close refusal (intentional theatrical behavior)
# ---------------------------------------------------------------------------


def test_close_refused_mid_attack(app):
    win = demo.MainWindow()
    try:
        win.speed_slider.setValue(30)
        win.start_attack()
        assert win.engine is not None and win.engine.isRunning()
        # The window refuses to close until the attack finishes.
        assert win.close() is False
        assert win.engine.isRunning()
    finally:
        win.engine.request_stop()
        win.engine.wait(15000)
        win.close()
        win.deleteLater()


# ---------------------------------------------------------------------------
# Full kill chain to completion (ransom dialog stubbed so the modal
# does not block the headless run)
# ---------------------------------------------------------------------------


class _StubRansomDialog:
    instances = []

    def __init__(self, parent, stats_text):
        self.stats_text = stats_text
        _StubRansomDialog.instances.append(self)

    def exec_(self):
        return 0


def _pump_until(spy, count=1, timeout_ms=120000):
    waited = 0
    while len(spy) < count and waited < timeout_ms:
        QTest.qWait(200)
        waited += 200
    assert len(spy) >= count, "attack did not finish in time"


def test_full_attack_runs_to_completion(app, monkeypatch):
    _StubRansomDialog.instances.clear()
    monkeypatch.setattr(demo, "RansomDialog", _StubRansomDialog)
    win = demo.MainWindow()
    try:
        win.speed_slider.setValue(30)
        win.start_attack()
        spy = QSignalSpy(win.engine.attack_finished)
        _pump_until(spy, timeout_ms=180000)
        assert win.stat_deleted.text() == "256"
        assert win.progress.value() == 100
        # The previously dead stats param now reaches the ransom dialog.
        assert _StubRansomDialog.instances
        stats_text = _StubRansomDialog.instances[0].stats_text
        assert "256" in stats_text and "deleted" in stats_text
        # Fresh launch resets state instead of stacking a second run.
        assert win.reset_btn.isEnabled()
    finally:
        if win.engine is not None and win.engine.isRunning():
            win.engine.request_stop()
            win.engine.wait(15000)
        win.close()
        win.deleteLater()


def test_reset_restores_pristine_state(app, monkeypatch):
    _StubRansomDialog.instances.clear()
    monkeypatch.setattr(demo, "RansomDialog", _StubRansomDialog)
    win = demo.MainWindow()
    try:
        win.speed_slider.setValue(30)
        win.start_attack()
        spy = QSignalSpy(win.engine.attack_finished)
        _pump_until(spy, timeout_ms=180000)
        win.reset_demo()
        QTest.qWait(500)
        assert win.stat_deleted.text() == "0"
        assert win.progress.value() == 0
        assert all(t.status == "clean" for t in win.vfs.targets)
        assert len(win._tree_items) == 256
    finally:
        if win.engine is not None and win.engine.isRunning():
            win.engine.request_stop()
            win.engine.wait(15000)
        win.close()
        win.deleteLater()
