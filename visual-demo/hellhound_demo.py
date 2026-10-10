#!/usr/bin/env python3
"""
HELLHOUND Visual Demo -- Deletion Virus Simulator
=================================================
A scary-looking EDUCATIONAL simulation of how a deletion virus operates,
built for live demonstration shows.

SIMULATION ONLY: everything happens inside a fully virtual (in-memory)
filesystem. No real files are read, modified, encrypted, or deleted.
Nothing on the host machine is touched, ever. The destruction you see
is real *within the simulation* -- every virtual file is genuinely
encrypted and deleted in the sim -- but it cannot reach your real files.

Each attack phase is narrated: what a real virus does at that stage,
and how defenders stop it. Warnings throughout.

Requires: Python 3.7+, PyQt5 (pip install PyQt5)
Run:  python hellhound_demo.py
"""

import sys
import threading
import time
import random
from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QBrush, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QSlider, QCheckBox, QProgressBar, QSplitter, QDialog,
)


# ---------------------------------------------------------------------------
# Assets (evil dog graphics live next to this script in assets/).
# When frozen with PyInstaller, bundled data lives under sys._MEIPASS.
# ---------------------------------------------------------------------------
_BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS_DIR = _BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "hellhound_logo.png"


def load_logo(size):
    """Return the hellhound logo as a scaled QPixmap, or None if missing."""
    if LOGO_PATH.is_file():
        pm = QPixmap(str(LOGO_PATH))
        if not pm.isNull():
            return pm.scaled(size, size, Qt.KeepAspectRatio,
                             Qt.SmoothTransformation)
    return None


# ---------------------------------------------------------------------------
# Educational content per attack phase
# ---------------------------------------------------------------------------
PHASES = [
    ("INFILTRATION",
     "What you're seeing: the payload lands on the machine -- usually via a "
     "phishing attachment, a trojanized download, or an infected USB drive. "
     "It quietly establishes persistence so it survives a reboot.",
     "How to stop it: email filtering, never run untrusted attachments or "
     "macros, keep software patched, disable autorun for removable media."),
    ("RECONNAISSANCE",
     "What you're seeing: the virus surveys the filesystem -- mapping drives, "
     "listing documents, pictures, and backups. It prioritizes valuable file "
     "types (.docx, .xlsx, .pdf, photos, databases) and notes backup locations "
     "to destroy later.",
     "How to stop it: least-privilege accounts (malware inherits YOUR "
     "permissions), EDR tools that flag mass file enumeration, and keeping "
     "backups offline or immutable so recon can't find them."),
    ("ENCRYPTION",
     "What you're seeing: files are encrypted in place (real ransomware uses "
     "AES-256). The originals become unreadable without the attacker's key. "
     "This happens BEFORE deletion so victims can't just undelete.",
     "How to stop it: offline / immutable backups (the 3-2-1 rule), "
     "application allowlisting, and behavioral detection that catches mass "
     "encryption early."),
    ("DELETION",
     "What you're seeing: the wiper phase. Files are deleted outright and "
     "shadow copies / recycle bins are purged so recovery tools find nothing. "
     "Wipers don't even want ransom -- just destruction.",
     "How to stop it: immutable backups that can't be deleted by the OS, "
     "network segmentation to contain the blast radius, and a tested incident "
     "response plan."),
    ("RANSOM NOTE",
     "What you're seeing: the payoff demand. A note appears with payment "
     "instructions and a countdown timer to pressure the victim into paying "
     "before thinking.",
     "How to stop it: never pay -- decryption is not guaranteed and payment "
     "funds the next attack. Restore from clean backups, report to law "
     "enforcement, and have an incident response plan BEFORE you need one."),
]


# ---------------------------------------------------------------------------
# Targets -- virtual (in-memory) files. Nothing on disk, ever.
# ---------------------------------------------------------------------------
@dataclass
class Target:
    dirpath: str        # display path (e.g. C:\Users\Victim\Documents)
    name: str
    size_kb: int
    status: str = "clean"   # clean -> found -> encrypted -> deleted


DIR_BLUEPRINT = {
    "C:\\Windows\\System32": [("dll", 14), ("sys", 10), ("exe", 8)],
    "C:\\Users\\Victim\\Documents": [("docx", 22), ("xlsx", 12), ("pdf", 16), ("txt", 10)],
    "C:\\Users\\Victim\\Pictures": [("jpg", 30), ("png", 18), ("mp4", 6)],
    "C:\\Users\\Victim\\Desktop": [("lnk", 8), ("docx", 6), ("pdf", 5)],
    "C:\\Users\\Victim\\Downloads": [("zip", 8), ("exe", 5), ("pdf", 6)],
    "C:\\Program Files\\Office": [("exe", 10), ("dll", 16)],
    "D:\\Backups": [("bak", 12), ("zip", 8)],
    "D:\\Projects": [("py", 14), ("db", 4), ("md", 8)],
}

NAME_WORDS = ["report", "invoice", "photo", "backup", "project", "data",
              "notes", "budget", "contract", "presentation", "archive",
              "database", "config", "draft", "final", "summer", "client"]


def generate_target_list(rng_seed=1337):
    """Deterministic list of virtual Targets. No disk I/O at all."""
    rng = random.Random(rng_seed)
    targets = []
    for dirpath, specs in DIR_BLUEPRINT.items():
        for ext, count in specs:
            for _ in range(count):
                name = f"{rng.choice(NAME_WORDS)}_{rng.randint(100, 999)}.{ext}"
                size = rng.randint(12, 8192)
                targets.append(Target(dirpath, name, size))
    return targets


class VirtualFS:
    """A fake filesystem that lives entirely in memory."""

    def __init__(self):
        self.targets = generate_target_list()

    @property
    def total_kb(self):
        return sum(t.size_kb for t in self.targets)


# ---------------------------------------------------------------------------
# Attack engine -- runs the SIMULATED attack on a worker thread
# ---------------------------------------------------------------------------
class AttackEngine(QThread):
    phase_changed = pyqtSignal(int)
    log_line = pyqtSignal(str, str)            # text, color
    file_found = pyqtSignal(int)               # index
    file_encrypted = pyqtSignal(int)           # index
    file_deleted = pyqtSignal(int)             # index
    stats_updated = pyqtSignal(int, int, int)  # deleted, encrypted, kb_destroyed
    attack_finished = pyqtSignal()

    def __init__(self, targets):
        super().__init__()
        self.targets = targets
        self.speed = 5
        self.do_encrypt = True
        self._stop_event = threading.Event()

    def set_speed(self, v):
        self.speed = max(1, v)

    def set_encrypt(self, c):
        self.do_encrypt = bool(c)

    def request_stop(self):
        self._stop_event.set()

    def _wait(self, seconds):
        target = seconds / self.speed
        step = 0.02
        waited = 0.0
        while waited < target and not self._stop_event.is_set():
            time.sleep(min(step, target - waited))
            waited += step

    def _log(self, text, color="#c8c8c8"):
        self.log_line.emit(text, color)

    def run(self):
        n = len(self.targets)
        deleted = encrypted = kb_destroyed = 0

        # -- Phase 0: Infiltration -------------------------------------
        self.phase_changed.emit(0)
        self._log("[SIM] Payload delivered via trojanized invoice.pdf.exe", "#ff5555")
        self._wait(0.8)
        self._log("[SIM] Establishing persistence (registry Run key)...", "#ff5555")
        self._wait(0.8)
        self._log("[+] Persistence established. Going quiet.", "#55ff55")
        self._wait(0.5)

        # -- Phase 1: Recon --------------------------------------------
        self.phase_changed.emit(1)
        self._log(f"[SIM] Enumerating filesystem -- {n} files discovered", "#ffaa00")
        for i, t in enumerate(self.targets):
            if self._stop_event.is_set():
                return
            t.status = "found"
            self.file_found.emit(i)
            if i % 40 == 0:
                self._log(f"    scanning {t.dirpath} ... {i}/{n}", "#888888")
            self._wait(0.030)
        self._log(f"[+] Targets prioritized: documents, photos, backups ({n} files)",
                  "#55ff55")

        # -- Phase 2: Encryption (optional) -----------------------------
        if self.do_encrypt:
            self.phase_changed.emit(2)
            self._log("[SIM] Encrypting files with AES-256 (simulated)...", "#ffaa00")
            for i, t in enumerate(self.targets):
                if self._stop_event.is_set():
                    return
                t.status = "encrypted"
                encrypted += 1
                self.file_encrypted.emit(i)
                if i % 50 == 0:
                    self._log(f"    encrypted {i}/{n}", "#888888")
                self.stats_updated.emit(deleted, encrypted, kb_destroyed)
                self._wait(0.025)
            self._log("[+] All files encrypted. Originals unrecoverable.", "#ff5555")

        # -- Phase 3: Deletion ------------------------------------------
        self.phase_changed.emit(3)
        self._log("[SIM] Wiper phase: deleting files, purging shadow copies...",
                  "#ff5555")
        for i, t in enumerate(self.targets):
            if self._stop_event.is_set():
                return
            t.status = "deleted"
            deleted += 1
            kb_destroyed += t.size_kb
            self.file_deleted.emit(i)
            if i % 40 == 0:
                self._log(f"    deleted {i}/{n}  ({kb_destroyed // 1024} MB gone)",
                          "#ff5555")
            self.stats_updated.emit(deleted, encrypted, kb_destroyed)
            self._wait(0.045)
        self._log("[+] Filesystem wiped. Shadow copies purged.", "#ff5555")

        # -- Phase 4: Ransom note ---------------------------------------
        self.phase_changed.emit(4)
        self._log("[SIM] Dropping ransom note: READ_ME_TO_RECOVER.txt", "#ffaa00")
        self._wait(0.6)
        self.attack_finished.emit()

# ---------------------------------------------------------------------------
# Ransom note dialog -- pops at the end of the attack
# ---------------------------------------------------------------------------
class RansomDialog(QDialog):
    def __init__(self, parent, stats_text):
        super().__init__(parent)
        self.setWindowTitle("READ_ME_TO_RECOVER.txt")
        self.setModal(True)
        self.resize(480, 560)
        self.setStyleSheet("""
            QDialog { background-color: #0a0000; border: 3px solid #ff0000; }
            QLabel { color: #ffdddd; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        logo = load_logo(150)
        if logo:
            logo_lbl = QLabel()
            logo_lbl.setPixmap(logo)
            logo_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_lbl)

        title = QLabel("YOUR FILES ARE GONE.")
        title.setAlignment(Qt.AlignCenter)
        f = QFont("Arial", 26, QFont.Bold)
        title.setFont(f)
        title.setStyleSheet("color: #ff0000; letter-spacing: 2px;")
        layout.addWidget(title)

        sub = QLabel("Every document, photo, and backup on this machine has been\n"
                     "encrypted with AES-256 and then wiped. Shadow copies purged.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #ffaaaa; font-size: 13px;")
        layout.addWidget(sub)

        self.timer_lbl = QLabel()
        self.timer_lbl.setAlignment(Qt.AlignCenter)
        self.timer_lbl.setStyleSheet("color: #ff0000; font-size: 34px; font-weight: bold;")
        layout.addWidget(self.timer_lbl)
        self._seconds_left = 72 * 3600
        self._tick_timer()
        self._qtimer = QTimer(self)
        self._qtimer.timeout.connect(self._tick_timer)
        self._qtimer.start(1000)

        pay = QLabel("Send 2.5 BTC to the address below within 72 hours\n"
                     "or the decryption key is destroyed forever.")
        pay.setAlignment(Qt.AlignCenter)
        pay.setWordWrap(True)
        pay.setStyleSheet("color: #ffcc66; font-size: 13px;")
        layout.addWidget(pay)

        addr = QLabel("bc1q-hellhound-demonstration-only-do-not-pay")
        addr.setAlignment(Qt.AlignCenter)
        addr.setStyleSheet("color: #888888; font-family: monospace; font-size: 12px;")
        layout.addWidget(addr)

        sim = QLabel("EDUCATIONAL SIMULATION -- no real files were harmed.\n"
                     "In a real attack there is no reset button.")
        sim.setAlignment(Qt.AlignCenter)
        sim.setWordWrap(True)
        sim.setStyleSheet("color: #666666; font-size: 11px; font-style: italic;")
        layout.addWidget(sim)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "QPushButton { background-color: #330000; color: #ff5555; "
            "border: 1px solid #ff0000; padding: 8px; font-weight: bold; }"
            "QPushButton:hover { background-color: #550000; }")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _tick_timer(self):
        h = self._seconds_left // 3600
        m = (self._seconds_left % 3600) // 60
        s = self._seconds_left % 60
        self.timer_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")
        if self._seconds_left > 0:
            self._seconds_left -= 1


# ---------------------------------------------------------------------------
# Main window -- the scary demo console
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HELLHOUND -- Deletion Virus Visual Demo")
        self.resize(1180, 860)
        logo = load_logo(64)
        if logo:
            self.setWindowIcon(QIcon(logo))

        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #050505; color: #e8e8e8; }
            QLabel { color: #e8e8e8; }
            QTreeWidget {
                background-color: #0a0a0a; color: #cccccc;
                border: 1px solid #440000; font-family: monospace; font-size: 11px;
            }
            QTreeWidget::item { padding: 1px; }
            QHeaderView::section {
                background-color: #1a0000; color: #ff6666;
                border: none; font-weight: bold; padding: 4px;
            }
            QTextEdit {
                background-color: #000000; color: #00ff66;
                border: 1px solid #003300; font-family: monospace; font-size: 11px;
            }
            QProgressBar {
                background-color: #1a0000; border: 1px solid #660000;
                text-align: center; color: #ffaaaa; height: 22px;
                font-weight: bold;
            }
            QProgressBar::chunk { background-color: #cc0000; }
            QSlider::groove:horizontal { background: #330000; height: 8px; }
            QSlider::handle:horizontal {
                background: #ff0000; width: 18px; margin: -5px 0;
                border-radius: 9px;
            }
            QCheckBox { color: #ffaaaa; font-weight: bold; spacing: 8px; }
            QPushButton {
                background-color: #1a0000; color: #ff6666;
                border: 1px solid #660000; padding: 8px 14px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #330000; border-color: #ff0000; }
            QPushButton:disabled { color: #553333; border-color: #331111; }
        """)

        self.vfs = VirtualFS()
        self.engine = None
        self._start_time = None
        self._tree_items = []

        self._build_ui()
        self._populate_tree()

    # -- UI construction -------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # Header: logo + title + SIM badge
        header = QHBoxLayout()
        logo_lbl = QLabel()
        pm = load_logo(110)
        if pm:
            logo_lbl.setPixmap(pm)
        else:
            logo_lbl.setText("\U0001f43a")
            logo_lbl.setStyleSheet("font-size: 72px;")
        header.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title = QLabel("HELLHOUND")
        title.setFont(QFont("Arial", 34, QFont.Bold))
        title.setStyleSheet("color: #ff0000; letter-spacing: 8px;")
        title_box.addWidget(title)
        subtitle = QLabel("DELETION VIRUS  \u2022  VISUAL DEMONSTRATION")
        subtitle.setFont(QFont("Arial", 12, QFont.Bold))
        subtitle.setStyleSheet("color: #aa3333; letter-spacing: 3px;")
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch(1)

        self.sim_badge = QLabel("  \u26a0 SIMULATION \u26a0  ")
        self.sim_badge.setFont(QFont("Arial", 13, QFont.Bold))
        self.sim_badge.setStyleSheet(
            "background-color: #ffcc00; color: #000000; padding: 8px;")
        header.addWidget(self.sim_badge, alignment=Qt.AlignTop)
        root.addLayout(header)

        # Warning strip
        warn = QLabel(
            "\u26a0 EDUCATIONAL DEMONSTRATION \u2014 all files shown are VIRTUAL. "
            "Nothing on this machine is being read, encrypted, or deleted. \u26a0")
        warn.setWordWrap(True)
        warn.setAlignment(Qt.AlignCenter)
        warn.setStyleSheet(
            "background-color: #2a1a00; color: #ffcc00; padding: 6px; "
            "border: 1px solid #ffcc00; font-weight: bold; font-size: 12px;")
        root.addWidget(warn)

        # Phase tracker pills
        tracker = QHBoxLayout()
        tracker.addStretch(1)
        self.phase_pills = []
        for name, _, _ in PHASES:
            pill = QLabel(f"  {name}  ")
            pill.setFont(QFont("Arial", 10, QFont.Bold))
            pill.setStyleSheet(
                "background-color: #1a1a1a; color: #666666; padding: 6px 4px; "
                "border: 1px solid #333333;")
            tracker.addWidget(pill)
            self.phase_pills.append(pill)
        tracker.addStretch(1)
        root.addLayout(tracker)

        # Education panel
        edu = QWidget()
        edu.setStyleSheet(
            "background-color: #0d0d0d; border: 1px solid #440000;")
        edu_layout = QVBoxLayout(edu)
        self.edu_seeing = QLabel()
        self.edu_seeing.setWordWrap(True)
        self.edu_seeing.setStyleSheet("color: #ffcc99; font-size: 12px; padding: 4px;")
        self.edu_defense = QLabel()
        self.edu_defense.setWordWrap(True)
        self.edu_defense.setStyleSheet("color: #99ff99; font-size: 12px; padding: 4px;")
        edu_layout.addWidget(self.edu_seeing)
        edu_layout.addWidget(self.edu_defense)
        root.addWidget(edu)
        self._set_phase_edu(-1)

        # Stats row
        stats = QHBoxLayout()
        self.stat_deleted = self._make_stat(stats, "FILES DELETED", "0")
        self.stat_encrypted = self._make_stat(stats, "FILES ENCRYPTED", "0")
        self.stat_data = self._make_stat(stats, "DATA DESTROYED", "0 MB")
        self.stat_rate = self._make_stat(stats, "DELETION RATE", "0 /s")
        root.addLayout(stats)

        # Splitter: file tree | attack log
        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File", "Size", "Status"])
        self.tree.setColumnWidth(0, 420)
        splitter.addWidget(self.tree)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        splitter.addWidget(self.log)
        splitter.setSizes([620, 560])
        root.addWidget(splitter, stretch=1)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("STANDBY -- press LAUNCH ATTACK")
        root.addWidget(self.progress)

        # Controls
        controls = QHBoxLayout()
        self.launch_btn = QPushButton("\U0001f525 LAUNCH ATTACK")
        self.launch_btn.setStyleSheet(
            "QPushButton { background-color: #660000; color: #ffffff; "
            "border: 2px solid #ff0000; padding: 10px 18px; font-size: 15px; }"
            "QPushButton:hover { background-color: #990000; }")
        self.launch_btn.clicked.connect(self.start_attack)
        controls.addWidget(self.launch_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_demo)
        controls.addWidget(self.reset_btn)

        controls.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 30)
        self.speed_slider.setValue(5)
        self.speed_slider.setFixedWidth(160)
        self.speed_slider.valueChanged.connect(self._on_speed)
        controls.addWidget(self.speed_slider)
        self.speed_lbl = QLabel("5x")
        self.speed_lbl.setFixedWidth(36)
        controls.addWidget(self.speed_lbl)

        self.encrypt_cb = QCheckBox("Ransomware mode (encrypt before wipe)")
        self.encrypt_cb.setChecked(True)
        controls.addWidget(self.encrypt_cb)

        controls.addStretch(1)
        root.addLayout(controls)

    def _make_stat(self, layout, label, value):
        box = QVBoxLayout()
        lab = QLabel(label)
        lab.setFont(QFont("Arial", 9, QFont.Bold))
        lab.setStyleSheet("color: #aa3333;")
        lab.setAlignment(Qt.AlignCenter)
        val = QLabel(value)
        val.setFont(QFont("Arial", 18, QFont.Bold))
        val.setStyleSheet("color: #ff0000;")
        val.setAlignment(Qt.AlignCenter)
        box.addWidget(lab)
        box.addWidget(val)
        layout.addLayout(box)
        return val

    # -- tree ------------------------------------------------------------
    def _populate_tree(self):
        self.tree.clear()
        self._tree_items = []
        dir_nodes = {}
        for idx, t in enumerate(self.vfs.targets):
            if t.dirpath not in dir_nodes:
                node = QTreeWidgetItem(self.tree, [t.dirpath, "", ""])
                node.setForeground(0, QBrush(QColor("#ffaa00")))
                f = QFont("monospace", 11, QFont.Bold)
                node.setFont(0, f)
                node.setExpanded(True)
                dir_nodes[t.dirpath] = node
            item = QTreeWidgetItem(dir_nodes[t.dirpath],
                                   [t.name, f"{t.size_kb} KB", "clean"])
            item.setForeground(2, QBrush(QColor("#666666")))
            self._tree_items.append(item)

    def _mark_item(self, idx, status, color, strike=False):
        if 0 <= idx < len(self._tree_items):
            item = self._tree_items[idx]
            item.setText(2, status)
            item.setForeground(2, QBrush(QColor(color)))
            font = item.font(0)
            font.setStrikeOut(strike)
            item.setFont(0, font)
            item.setFont(1, font)
            item.setFont(2, font)

    # -- education panel ---------------------------------------------------
    def _set_phase_edu(self, phase_idx):
        for i, pill in enumerate(self.phase_pills):
            if i == phase_idx:
                pill.setStyleSheet(
                    "background-color: #660000; color: #ffffff; padding: 6px 4px; "
                    "border: 2px solid #ff0000;")
            elif 0 <= phase_idx and i < phase_idx:
                pill.setStyleSheet(
                    "background-color: #2a0000; color: #ff6666; padding: 6px 4px; "
                    "border: 1px solid #660000;")
            else:
                pill.setStyleSheet(
                    "background-color: #1a1a1a; color: #666666; padding: 6px 4px; "
                    "border: 1px solid #333333;")
        if 0 <= phase_idx < len(PHASES):
            name, seeing, defense = PHASES[phase_idx]
            self.edu_seeing.setText(f"\u25b6  <b>{seeing}</b>")
            self.edu_defense.setText(f"\u2714  <b>{defense}</b>")
        else:
            self.edu_seeing.setText(
                "\u25b6  Press LAUNCH ATTACK to watch a simulated "
                "deletion virus work through its kill chain -- safely, on virtual files.")
            self.edu_defense.setText(
                "\u2714  Each phase explains how defenders stop the real thing.")

    # -- controls ----------------------------------------------------------
    def _on_speed(self, v):
        self.speed_lbl.setText(f"{v}x")
        if self.engine:
            self.engine.set_speed(v)

    def start_attack(self):
        if self.engine and self.engine.isRunning():
            return
        # Fresh kill chain every launch: wipe any previous run's markings.
        self._reset_state()
        self._log_line("=" * 60, "#ff0000")
        self._log_line("[!] HELLHOUND SIMULATION STARTING -- virtual files only", "#ff0000")
        self._log_line("[i] Nothing on this machine will be touched.", "#ffcc00")
        self._log_line("=" * 60, "#ff0000")
        self.engine = AttackEngine(self.vfs.targets)
        self.engine.set_speed(self.speed_slider.value())
        self.engine.set_encrypt(self.encrypt_cb.isChecked())
        self.engine.phase_changed.connect(self._on_phase)
        self.engine.log_line.connect(self._log_line)
        self.engine.file_found.connect(
            lambda i: self._mark_item(i, "FOUND", "#ffaa00"))
        self.engine.file_encrypted.connect(
            lambda i: self._mark_item(i, "\U0001f512 ENCRYPTED", "#ff8800"))
        self.engine.file_deleted.connect(
            lambda i: self._mark_item(i, "DELETED", "#ff0000", strike=True))
        self.engine.stats_updated.connect(self._on_stats)
        self.engine.attack_finished.connect(self._on_finished)
        self._start_time = time.time()
        self.reset_btn.setEnabled(False)
        self.encrypt_cb.setEnabled(False)
        self.launch_btn.setEnabled(False)
        self.progress.setFormat("ATTACK IN PROGRESS -- %p%")
        self.engine.start()

    def _reset_state(self):
        """Restore a pristine virtual filesystem, tree, stats, and progress."""
        self.vfs = VirtualFS()
        self._populate_tree()
        self.log.clear()
        self.stat_deleted.setText("0")
        self.stat_encrypted.setText("0")
        self.stat_data.setText("0 MB")
        self.stat_rate.setText("0 /s")
        self.progress.setValue(0)
        self.progress.setFormat("STANDBY -- press LAUNCH ATTACK")
        self._set_phase_edu(-1)
        self.reset_btn.setEnabled(True)
        self.encrypt_cb.setEnabled(True)
        self.launch_btn.setEnabled(True)

    def reset_demo(self):
        if self.engine and self.engine.isRunning():
            self.engine.request_stop()
            self.engine.wait(5000)
        self._reset_state()
        self._log_line("[i] Demo reset. Virtual filesystem restored.", "#55ff55")

    def closeEvent(self, event):
        # There is no shutting it down mid-attack. It runs until destruction.
        if self.engine and self.engine.isRunning():
            event.ignore()
            self._log_line("[!] You can't close HellHound. "
                           "It finishes what it started.", "#ff0000")
            return
        event.accept()

    # -- engine slots --------------------------------------------------------
    def _log_line(self, text, color):
        self.log.append(f'<span style="color:{color};">{text}</span>')

    def _on_phase(self, idx):
        self._set_phase_edu(idx)

    def _on_stats(self, deleted, encrypted, kb):
        n = len(self.vfs.targets)
        self.stat_deleted.setText(str(deleted))
        self.stat_encrypted.setText(str(encrypted))
        mb = kb / 1024
        self.stat_data.setText(f"{mb:,.1f} MB" if mb >= 1 else f"{kb} KB")
        elapsed = max(0.1, time.time() - (self._start_time or time.time()))
        self.stat_rate.setText(f"{deleted / elapsed:.0f} /s")
        total_ops = n + (n if self.engine and self.engine.do_encrypt else 0)
        done = deleted + encrypted
        pct = int(100 * done / max(1, total_ops))
        self.progress.setValue(pct)

    def _on_finished(self):
        self.progress.setValue(100)
        self.progress.setFormat("TOTAL DESTRUCTION -- 100%")
        self.reset_btn.setEnabled(True)
        self.encrypt_cb.setEnabled(True)
        self.launch_btn.setEnabled(True)
        stats_text = (f"{self.stat_deleted.text()} files deleted, "
                      f"{self.stat_data.text()} destroyed")
        self._log_line("", "#ff0000")
        self._log_line("Hellhound Fetched Their souls.", "#ff0000")
        self._log_line("Hard drives will Rott in Hell.", "#ff0000")
        self._log_line("Goodbye My Pup.", "#ff0000")
        RansomDialog(self, stats_text).exec_()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
