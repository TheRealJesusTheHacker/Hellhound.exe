# HELLHOUND

[![CI](https://github.com/TheRealJesusTheHacker/Hellhound.exe/actions/workflows/ci.yml/badge.svg)](https://github.com/TheRealJesusTheHacker/Hellhound.exe/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/TheRealJesusTheHacker/Hellhound.exe?label=latest%20release)](https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/latest)
[![License: MIT](https://img.shields.io/github/license/TheRealJesusTheHacker/Hellhound.exe)](LICENSE)

A blood-red PyQt5 **visual simulation of a ransomware kill chain** —
infiltration → reconnaissance → encryption → deletion → ransom note —
played out live against 256 virtual files in an in-memory filesystem.

## ⚠ EDUCATIONAL DEMONSTRATION — READ THIS FIRST

**This demo never touches real files.** Everything happens inside a fully
virtual (in-memory) filesystem: 256 fake files with a deterministic seed,
~1 GB of fake data, zero disk I/O. Nothing on your machine is read,
encrypted, modified, or deleted — ever. The destruction you watch is real
*within the simulation* (every virtual file is genuinely encrypted and
deleted in the sim), but it cannot reach your real files. A yellow
⚠ SIMULATION ⚠ badge and warning strips say so throughout the app.

Educational purposes only. The authors assume no liability for misuse.

## What this is, and why it exists

Most people understand ransomware as an abstract threat: *"your files get
encrypted."* HELLHOUND makes the kill chain **visible**. Built for live
demonstration shows and security education, it walks an audience through
exactly how a deletion virus works — how it lands, how it maps your files,
why it encrypts *before* it wipes, how it destroys your backups so you
can't recover, and how the ransom note manufactures panic. And at every
phase, the screen tells you **how defenders stop it**. It's a teaching
stage, not a weapon: scary on purpose, harmless by construction.

## Who it's for

- **Students and bootcamp learners** studying malware behavior, kill chains,
  and incident response.
- **Educators and speakers** who need a live, visual ransomware demo that is
  safe to run on stage in front of an audience.
- **Security teams** onboarding defenders: each phase explains the attack
  *and* the countermeasure, so blue-team lessons land visually.
- **Content creators** explaining ransomware to non-technical audiences —
  the demo narrates itself in plain language.

## How it works

Two pieces run side by side:

**`VirtualFS` — the fake filesystem.** 256 `Target` objects (path, name,
size) generated deterministically from seed `1337`, spread across 8 fake
directories — `C:\Windows\System32`, `C:\Users\Victim\Documents`,
`C:\Users\Victim\Pictures`, `C:\Users\Victim\Desktop`,
`C:\Users\Victim\Downloads`, `C:\Program Files\Office`, `D:\Backups`,
`D:\Projects`. File sizes are randomized between 12 KB and 8 MB, totaling
~1 GB of fake data. It lives entirely in RAM; the generator performs no
disk I/O at all.

**`AttackEngine` — the simulated attacker.** A `QThread` that walks the
kill chain and emits batched Qt signals (`phase_changed`, `files_found`,
`files_encrypted`, `files_deleted`, `stats_updated`, `attack_finished`).
At speed ≤ 5× every file is animated individually; above that, signals are
batched (25 per flush) and stats repaint at most ~10 Hz so the GUI never
chokes. Stop is a `threading.Event`, so halting never blocks the UI.

The **PyQt5 console** subscribes to those signals and renders the attack:
tree markings, terminal log, stats, progress, and phase education panels —
all live.

## The kill chain, phase by phase

Each phase lights up a tracker pill and fills an education panel with two
lines: **what you're seeing** and **how defenders stop it**.

### 1. Infiltration
The log shows the payload landing — *"trojanized invoice.pdf.exe"* — and
establishing persistence via a registry Run key, then going quiet.
**Defense lesson:** email filtering, never run untrusted attachments or
macros, keep software patched, disable autorun for removable media.

### 2. Reconnaissance
The virus enumerates the filesystem — all 256 files discovered — and
prioritizes valuable types (`.docx`, `.xlsx`, `.pdf`, photos, databases),
noting backup locations to destroy later. Tree items flip from `clean`
to **FOUND** (gold).
**Defense lesson:** least-privilege accounts (malware inherits *your*
permissions), EDR flagging mass file enumeration, offline or immutable
backups that recon can't find.

### 3. Encryption (ransomware mode)
Files are "encrypted" in place — the log narrates AES-256, like real
ransomware — and originals become unreadable without the attacker's key.
This happens **before** deletion so victims can't just undelete. Tree items
flip to **🔒 ENCRYPTED** (orange). This phase is a toggle (see Controls).
**Defense lesson:** offline / immutable backups (the 3-2-1 rule),
application allowlisting, behavioral detection catching mass encryption
early.

### 4. Deletion
The wiper phase: files deleted outright, shadow copies and recycle bins
purged so recovery tools find nothing. Tree items flip to **DELETED**
(red, struck through). The log narrates: *"Wipers don't even want ransom
— just destruction."*
**Defense lesson:** immutable backups the OS can't delete, network
segmentation to contain the blast radius, a tested incident response plan.

### 5. Ransom note
`READ_ME_TO_RECOVER.txt` drops: a modal dialog with a live 72:00:00
countdown ticking down every second, a demand of **2.5 BTC** to a fake
demonstration address (`bc1q-hellhound-demonstration-only-do-not-pay` —
do not pay), the attack stats (files deleted, data destroyed), and the
sign-off in blood-red terminal text:

> Hellhound Fetched Their souls.
> Hard drives will Rott in Hell.
> Goodbye My Pup.

**Defense lesson:** never pay — decryption isn't guaranteed and payment
funds the next attack. Restore from clean backups, report to law
enforcement, have an incident response plan *before* you need one.

## The console UI

Everything on screen serves the demo:

- **Header** — hellhound logo, `HELLHOUND` title, `DELETION VIRUS •
  VISUAL DEMONSTRATION` subtitle, and the yellow **⚠ SIMULATION ⚠**
  badge.
- **Warning strip** — *"⚠ EDUCATIONAL DEMONSTRATION — all files shown
  are VIRTUAL. Nothing on this machine is being read, encrypted, or
  deleted. ⚠"*
- **Phase tracker** — five pills (INFILTRATION, RECONNAISSANCE,
  ENCRYPTION, DELETION, RANSOM NOTE) lighting up as the attack advances.
- **Education panel** — per phase: ▶ what you're seeing, ✔ how
  defenders stop it.
- **Kill stats** — FILES DELETED, FILES ENCRYPTED, DATA DESTROYED
  (KB/MB), DELETION RATE (files/sec), updating live.
- **File tree** — File / Size / Status columns; directories in gold;
  each file marches `clean → FOUND → 🔒 ENCRYPTED → DELETED` (red,
  struck through).
- **Attack log** — green-on-black terminal with colored entries narrating
  every move ("[SIM] Payload delivered via trojanized invoice.pdf.exe",
  progress checkpoints every 40–50 files, "Shadow copies purged").
- **Progress bar** — `STANDBY — press LAUNCH ATTACK` → `ATTACK IN
  PROGRESS — %` → `TOTAL DESTRUCTION — 100%`.

### Controls

- **🔥 LAUNCH ATTACK** — starts the kill chain (fresh virtual filesystem
  every launch).
- **Reset** — restores a pristine virtual filesystem, tree, stats, and
  progress; non-blocking (the engine halts on its own thread first).
- **Speed slider (1–30×)** — 1× for slow dramatic walkthroughs, 30× for a
  full run in seconds; adjustable live, mid-attack.
- **Ransomware mode (encrypt before wipe)** — checkbox, on by default;
  uncheck it and the attack skips the encryption phase (wiper-only run).

### No escape (intentional)

Like the real thing, there is no shutting it down once launched: **no
pause button**, Reset and Launch die mid-attack, and the window's close
button refuses until destruction is complete — *"You can't close
HellHound. It finishes what it started."* This theatrical behavior is
deliberate and covered by tests; it is not a bug.

## Install and run

Requirements: Python 3.7+, PyQt5.

```bash
# from the repo root
pip install -r visual-demo/requirements.txt
python visual-demo/hellhound_demo.py
```

Press **🔥 LAUNCH ATTACK**. Drag the speed slider for a slow dramatic
walkthrough (1×) or a full run in seconds (30×).

### Or run the Windows build

Grab **Hellhound.exe** from the
[Releases page](https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/latest).
Built automatically with PyInstaller on every release — every release
carries a signed build-provenance attestation.

> 📸 **Screenshot / demo GIF:** coming soon — a real capture of the demo
> in action will be added here.

## Verify it yourself

The demo ships with a headless test suite (pytest, `QT_QPA_PLATFORM=offscreen`)
that exercises the deterministic virtual filesystem, builds the full UI
offscreen, runs a complete kill chain to destruction, verifies reset, and
confirms the intentional mid-attack close refusal:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
```

Lint and format are enforced in CI (`ruff` + `black`, see `pyproject.toml`):

```bash
ruff check visual-demo tests
black --check visual-demo tests
```

## Project layout

```
.
├── visual-demo/
│   ├── hellhound_demo.py      # the whole demo, single file (PyQt5)
│   ├── requirements.txt       # PyQt5, pinned
│   ├── README.md              # demo-focused overview
│   └── assets/
│       ├── hellhound_logo.png # evil dog artwork (header, icon, ransom note)
│       └── hellhound.ico      # Windows exe icon
├── tests/                     # headless pytest suite (offscreen Qt)
├── .github/workflows/
│   ├── ci.yml                 # tests + ruff + black (push/PR)
│   ├── build-exe.yml          # builds Hellhound.exe on release
│   └── codeql.yml             # CodeQL scanning
├── CHANGELOG.md               # Keep a Changelog
├── SECURITY.md                # how to report vulnerabilities
└── LICENSE                    # MIT
```

Note: the repo root also contains `HellHound.py`, which is deliberately
left untouched and is not described in this README — this document covers
the visual demo only.

## Changelog & security

- [CHANGELOG.md](CHANGELOG.md) — Keep a Changelog format, seeded from git
  history.
- [SECURITY.md](SECURITY.md) — found a vulnerability? Report it privately
  to **Sentinelsafeguard@outlook.com**.

## Contact

Business inquiries: **Sentinelsafeguard@outlook.com** — Skyler Henderson,
Sentinel Safeguard LLC.

## License

MIT — see [LICENSE](LICENSE).

---

*HELLHOUND is an educational simulation. In a real attack there is no
reset button: keep offline backups, patch your systems, and have an
incident response plan before you need one.*

## Donations

If this tool earned its keep, BTC is welcome:

```
bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0
```
