# ⚠ WARNING — READ THIS FIRST

**The root program in this repository, `HellHound.py`, destroys real
files. That part is not a simulation.**

When you run `HellHound.py` and confirm, it permanently deletes real
files from real directories on the machine it runs on — and in
encryption mode it encrypts each file first, then deletes it. There is
**no undo**, no recycle-bin restore, and no recovery feature. Deleted
files are gone.

What it targets (only directories that exist are processed):

- **Windows:** `%USERPROFILE%\AppData\Local\Temp`,
  `%USERPROFILE%\Downloads`, `%USERPROFILE%\Desktop`, and
  `%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Recent`
- **Linux / macOS:** `/tmp`, `~/.cache`, and `~/.local/share/Trash`

Up to 5,000 files per directory tree are processed, and subdirectories
left empty are removed.

**Only run it on a machine you own, with files you can afford to lose
permanently.** Never run it on a machine — or a user account — whose
Downloads, Desktop, or other targeted files matter to you or to anyone
else. Use a throwaway machine, a VM, or a test account, and read the
target list it prints before you confirm.

The second program in this repository, the **visual demo** in
`visual-demo/`, is the opposite: it is a simulation only and never
touches real files. The two programs are documented separately below —
do not confuse them.

---

# HELLHOUND

An **education tool** that shows — visibly, step by step, with nothing
hidden — exactly what real destructive malware does.

[![CI](https://img.shields.io/github/actions/workflow/status/TheRealJesusTheHacker/Hellhound.exe/ci.yml?style=flat-square)](https://github.com/TheRealJesusTheHacker/Hellhound.exe/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/TheRealJesusTheHacker/Hellhound.exe/codeql.yml?style=flat-square&label=CodeQL)](https://github.com/TheRealJesusTheHacker/Hellhound.exe/actions/workflows/codeql.yml)
[![Latest release](https://img.shields.io/github/v/release/TheRealJesusTheHacker/Hellhound.exe?style=flat-square&label=latest%20release)](https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/latest)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: Proprietary](https://img.shields.io/badge/license-PROPRIETARY-red?style=flat-square)](LICENSE)

## Overview

Most people understand destructive malware as an abstract threat:
*"your files get deleted."* Hellhound makes it concrete. It exists so
students, educators, and defenders can **see exactly what real malware
does** — how it enumerates files, why ransomware encrypts *before* it
deletes, how parallel processing makes destruction fast, and how
defenders stop it.

Hellhound is "fictional malware" in exactly one sense: its story is
invented, and it announces and visualizes everything it does instead of
hiding like real malware would. It is judged on the quality of its
warnings, its consent flow, its announced-vs-actual scope, and the fact
that nothing it does is silent. Everything is up front: warnings before
it runs, the exact scope before consent, live narration while it works,
and a written report after it finishes. Nothing is a surprise — that
honesty is the point of the tool.

This repository contains **two distinct programs**:

1. **`HellHound.py`** (repository root) — a command-line demonstrator
   that performs **real** file encryption and **real** file deletion
   on the machine it runs on. See the warning at the top of this page.
2. **`visual-demo/`** — a blood-red PyQt5 **visual simulation** of a
   ransomware kill chain, played out against virtual files in memory.
   The demo never touches real files; the command-line tool does.

## The two programs at a glance

| | `HellHound.py` (root) | Visual demo (`visual-demo/`) |
|---|---|---|
| Touches real files | **Yes — encrypts and/or deletes them** | Never — fully virtual, in-memory filesystem |
| Interface | Command line | PyQt5 GUI (also shipped as `Hellhound.exe`) |
| Subject | Real destructive mechanics: threaded deletion, encrypt-before-delete | A staged ransomware kill chain: infiltration → recon → encryption → deletion → ransom note |
| Run it | `python HellHound.py` | `python visual-demo/hellhound_demo.py`, or the release executable |
| Version | 2.0, plus further fixes in progress (see CHANGELOG) | 1.4.0 |

## Who it's for

- **Students and bootcamp learners** studying malware behavior, kill
  chains, and incident response.
- **Educators and speakers** who need a live, visual ransomware demo
  that is safe to run on stage in front of an audience (the visual
  demo).
- **Security teams** onboarding defenders: each phase of the visual
  demo explains the attack *and* the countermeasure, so blue-team
  lessons land visually.
- **Content creators** explaining ransomware to non-technical
  audiences — the visual demo narrates itself in plain language.
- **Students of the real thing** who run `HellHound.py` on a throwaway
  machine or VM to watch actual threaded deletion and
  encrypt-before-delete behavior on files they can afford to lose.

---

## Program 1: `HellHound.py` — the real destructive demonstrator

Cross-platform (Windows, Linux, macOS), single file, built for the
command line.

### Features

- **Two modes, chosen up front:** deletion only, or encryption +
  deletion — the ransomware order of operations, done in the open.
- **Real encryption:** in encryption mode each file is encrypted in
  place with Fernet (AES-128-CBC with HMAC-SHA256, from the
  `cryptography` library) immediately before it is deleted. The tool
  names the cipher it actually uses.
- **Threaded processing:** files are processed by a
  `ThreadPoolExecutor` with 16 workers, submitted in a bounded window
  rather than all at once.
- **Announced scope and caps:** the exact target directories are
  printed before consent, processing is capped at 5,000 files per
  directory tree, and hitting the cap is announced before processing
  starts — remaining files are *not* processed, and that is stated,
  not silent.
- **Nothing fails silently:** directories that cannot be scanned are
  announced by name and counted as errors; a worker that fails
  unexpectedly is counted and announced; the final summary reports the
  true error count.
- **A written record of every run:** a console summary plus a
  machine-readable JSON report (`hellhound_report.json`). If a run
  fails after it has started, a report is still written, so the
  destruction that already happened is recorded; if the report itself
  cannot be written, that failure is announced too.

### Install and run

Requirements: Python 3.8+ and the `cryptography` library.

```bash
# from the repo root
pip install --require-hashes -r requirements.lock.txt
python HellHound.py
```

Then choose the mode, read the target directories it prints, and type
`YES` only if you accept losing those files permanently.

### How it works

- **Consent first.** The banner, mode choice, target list, and `YES`
  confirmation all happen before anything is touched (see
  [Safety model](#safety-model)).
- **Scan first.** Each target tree is walked and its files collected
  before processing starts. Directories that cannot be scanned are
  announced by name — with a note that their contents were *not*
  processed — and counted as errors; a run never reports a partial
  tree as "complete" in silence.
- **Threaded deletion.** Files are processed by a `ThreadPoolExecutor`
  with 16 workers, submitted in a bounded window (at most 64 futures
  in flight) rather than all at once. Each worker checks its file with
  a single `lstat`: only regular files are touched — symlinks are
  never followed or deleted. Progress is announced every 50 files.
- **Encryption mode (optional).** With mode 2, each file is encrypted
  in place with Fernet immediately before it is deleted. If a single
  file's encryption fails (for example, a file larger than available
  RAM, which is read fully into memory), the error is counted and
  reported in the summary, and the file is still deleted. Zero-byte
  files are skipped by the encryption step and deleted like the rest.
- **Cleanup.** After a tree is processed, its now-empty subdirectories
  are removed bottom-up.

### What a run leaves behind

- The deleted files and emptied directories are **gone** — that is the
  demonstration.
- `hellhound_report.json` — a machine-readable report: tool version
  (2.0), platform, timestamps, files/directories deleted, files
  encrypted, data volumes, execution time, error
  count, and the educational context (techniques used, standard
  mitigations).
- `hellhound_key.key` — in encryption mode, the Fernet key file
  described under [Configuration](#configuration). It is **not** a
  recovery mechanism: encryption is immediately followed by deletion.
- A console summary with the same destruction, encryption, and
  performance metrics (plus the deletion rate, which is shown in the
  console summary only).

---

## Program 2: the visual demo — simulation only

**This demo never touches real files.** Everything happens inside a
fully virtual (in-memory) filesystem: 256 fake files with a
deterministic seed, ~1 GB of fake data, zero disk I/O. Nothing on your
machine is read, encrypted, modified, or deleted — ever. The
destruction you watch is real *within the simulation* (every virtual
file is genuinely marked encrypted and deleted in the sim), but it
cannot reach your real files. A yellow ⚠ SIMULATION ⚠ badge and
warning strips say so throughout the app.

Most people understand ransomware as an abstract threat: *"your files
get encrypted."* The demo makes the kill chain **visible**. Built for
live demonstration shows and security education, it walks an audience
through exactly how a deletion virus works — how it lands, how it maps
your files, why it encrypts *before* it wipes, how it destroys your
backups so you can't recover, and how the ransom note manufactures
panic. And at every phase, the screen tells you **how defenders stop
it**. It's a teaching stage, not a weapon: scary on purpose, harmless
by construction.

Educational purposes only. The authors assume no liability for misuse.

### Features

- **Five-phase kill chain**, each phase with a plain-language
  explanation of what you're seeing and how defenders stop it.
- **Live console:** file tree marking every virtual file
  `clean → FOUND → 🔒 ENCRYPTED → DELETED`, a terminal-style attack
  log, kill stats, and a progress bar — all updating in real time.
- **Controls that teach pacing:** a 1–30× speed slider (adjustable
  live) and a ransomware-mode toggle (encrypt before wipe, on by
  default; uncheck it for a wiper-only run).
- **Deterministic stage set:** the same 256 virtual files across the
  same 8 fake directories on every launch, so a talk is rehearsable.
- **Windows executable:** the demo is also built with PyInstaller and
  attached to each release as `Hellhound.exe`, with a signed
  build-provenance attestation.

### Install and run the visual demo

Requirements: Python 3.7+, PyQt5 (pinned in
`visual-demo/requirements.txt`).

```bash
# from the repo root
pip install --require-hashes -r visual-demo/requirements.lock.txt
python visual-demo/hellhound_demo.py
```

Press **🔥 LAUNCH ATTACK**. Drag the speed slider for a slow dramatic
walkthrough (1×) or a full run in seconds (30×).

#### Or run the Windows build

Grab **Hellhound.exe** from the
[Releases page](https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/latest).
It is built automatically with PyInstaller on every release, and every
release build carries a signed build-provenance attestation. All
published releases to date package the visual demo.

> 📸 **Screenshot / demo GIF:** coming soon — a real capture of the
> demo in action will be added here.

### How it works

Two pieces run side by side:

**`VirtualFS` — the fake filesystem.** 256 `Target` objects (path,
name, size) generated deterministically from seed `1337`, spread
across 8 fake directories — `C:\Windows\System32`,
`C:\Users\Victim\Documents`, `C:\Users\Victim\Pictures`,
`C:\Users\Victim\Desktop`, `C:\Users\Victim\Downloads`,
`C:\Program Files\Office`, `D:\Backups`, `D:\Projects`. File sizes
are randomized between 12 KB and 8 MB, totaling ~1 GB of fake data.
It lives entirely in RAM; the generator performs no disk I/O at all.

**`AttackEngine` — the simulated attacker.** A `QThread` that walks
the kill chain and emits batched Qt signals (`phase_changed`,
`files_found`, `files_encrypted`, `files_deleted`, `stats_updated`,
`attack_finished`). At speed ≤ 5× every file is animated individually;
above that, signals are batched (25 per flush) and stats repaint at
most ~10 Hz so the GUI never chokes.

The **PyQt5 console** subscribes to those signals and renders the
attack: tree markings, terminal log, stats, progress, and phase
education panels — all live.

### The kill chain, phase by phase

Each phase lights up a tracker pill and fills an education panel with
two lines: **what you're seeing** and **how defenders stop it**.

#### 1. Infiltration

The log shows the payload landing — *"trojanized invoice.pdf.exe"* —
and establishing persistence via a registry Run key, then going quiet.
**Defense lesson:** email filtering, never run untrusted attachments
or macros, keep software patched, disable autorun for removable media.

#### 2. Reconnaissance

The virus enumerates the filesystem — all 256 files discovered — and
prioritizes valuable types (`.docx`, `.xlsx`, `.pdf`, photos,
databases), noting backup locations to destroy later. Tree items flip
from `clean` to **FOUND** (gold).
**Defense lesson:** least-privilege accounts (malware inherits *your*
permissions), EDR flagging mass file enumeration, offline or immutable
backups that recon can't find.

#### 3. Encryption (ransomware mode)

Files are "encrypted" in place — the narration describes AES-256, the
cipher real ransomware typically uses — and originals become
unreadable without the attacker's key. This happens **before**
deletion so victims can't just undelete. Tree items flip to
**🔒 ENCRYPTED** (orange). This phase is a toggle (see Controls).
Note: the demo's encryption is simulated — no real cryptography is
performed on anything.
**Defense lesson:** offline / immutable backups (the 3-2-1 rule),
application allowlisting, behavioral detection catching mass
encryption early.

#### 4. Deletion

The wiper phase: files deleted outright, shadow copies and recycle
bins purged so recovery tools find nothing. Tree items flip to
**DELETED** (red, struck through). The log narrates: *"Wipers don't
even want ransom — just destruction."*
**Defense lesson:** immutable backups the OS can't delete, network
segmentation to contain the blast radius, a tested incident response
plan.

#### 5. Ransom note

`READ_ME_TO_RECOVER.txt` drops: a modal dialog with a live 72:00:00
countdown ticking down every second, a demand of **2.5 BTC** to a fake
demonstration address (`bc1q-hellhound-demonstration-only-do-not-pay`
— do not pay), the attack stats (files deleted, data destroyed), and
the sign-off in blood-red terminal text:

> Hellhound Fetched Their souls.
> Hard drives will Rott in Hell.
> Goodbye My Pup.

**Defense lesson:** never pay — decryption isn't guaranteed and
payment funds the next attack. Restore from clean backups, report to
law enforcement, have an incident response plan *before* you need
one.

### The console UI

Everything on screen serves the demo:

- **Header** — hellhound logo, `HELLHOUND` title, `DELETION VIRUS •
  VISUAL DEMONSTRATION` subtitle, and the yellow **⚠ SIMULATION ⚠**
  badge.
- **Warning strip** — *"⚠ EDUCATIONAL DEMONSTRATION — all files shown
  are VIRTUAL. Nothing on this machine is being read, encrypted, or
  deleted. ⚠"*
- **Phase tracker** — five pills (INFILTRATION, RECONNAISSANCE,
  ENCRYPTION, DELETION, RANSOM NOTE) lighting up as the attack
  advances.
- **Education panel** — per phase: ▶ what you're seeing, ✔ how
  defenders stop it.
- **Kill stats** — FILES DELETED, FILES ENCRYPTED, DATA DESTROYED
  (KB/MB), DELETION RATE (files/sec), updating live.
- **File tree** — File / Size / Status columns; directories in gold;
  each file marches `clean → FOUND → 🔒 ENCRYPTED → DELETED` (red,
  struck through).
- **Attack log** — green-on-black terminal with colored entries
  narrating every move ("[SIM] Payload delivered via trojanized
  invoice.pdf.exe", progress checkpoints during each phase, "Shadow
  copies purged").
- **Progress bar** — `STANDBY — press LAUNCH ATTACK` → `ATTACK IN
  PROGRESS — %` → `TOTAL DESTRUCTION — 100%`.

### Controls

- **🔥 LAUNCH ATTACK** — starts the kill chain (fresh virtual
  filesystem every launch).
- **Reset** — restores a pristine virtual filesystem, tree, stats,
  and progress.
- **Speed slider (1–30×)** — 1× for slow dramatic walkthroughs, 30×
  for a full run in seconds; adjustable live, mid-attack. Default 5×.
- **Ransomware mode (encrypt before wipe)** — checkbox, on by
  default; uncheck it and the attack skips the encryption phase
  (wiper-only run).

### No escape (intentional)

Like the real thing, there is no shutting the demo down once launched:
**no pause button**, Launch / Reset / the ransomware-mode toggle are
disabled while an attack is running, and the window's close button
refuses until destruction is complete — *"You can't close HellHound.
It finishes what it started."* This theatrical behavior is deliberate
and covered by tests; it is not a bug.

---

## Safety model

Hellhound's safety model is honesty, not harmlessness — the root tool
really destroys files. It is built so that **nothing is a surprise and
nothing happens silently**:

### The consent flow — nothing happens silently

Before `HellHound.py` touches a single file:

1. A warning banner states plainly that this is a destructive tool
   for educational use only.
2. You choose the mode — **1) deletion only** or **2) encryption +
   deletion**. An unrecognized choice exits immediately; nothing is
   touched and there is no silent fallback to a destructive mode.
3. The **exact target directories are printed before the confirmation
   prompt**, so consent is given against the real scope.
4. You must type **`YES`** to proceed. Anything else cancels the run.
5. During the run, every action is logged to the console in real
   time — scanning, progress checkpoints every 50 files, errors, and
   limits are all announced, never silent.

### Announced scope and caps

- Only the platform target directories listed in the warning exist in
  scope, and only directories that actually exist are processed.
- At most **5,000 files per directory tree** are processed. Reaching
  the cap is announced before processing starts, naming the files that
  will *not* be processed.
- Subdirectories left empty are removed; the target directories
  themselves are the roots that get processed.
- Symlinks are never followed or deleted by the deletion worker.

### Failures are counted, not hidden

- A directory that cannot be scanned is announced by name, counted as
  an error, and reported as *not processed*.
- A file whose encryption fails is counted in the run's error total
  and reported in the summary (the file is still deleted, as
  announced).
- A worker that fails unexpectedly is counted and announced — the
  summary never claims a clean run that wasn't.
- A run that fails after starting still writes its JSON report; a
  report that cannot be written is announced.

### The key file

In encryption mode, the Fernet key is written to `hellhound_key.key`
in the working directory (generated on first use, loaded after that).
If that file exists but is corrupt, the tool refuses to run and
touches nothing until you delete the key file yourself.

### The visual demo's safety model

The visual demo's model is construction, not consent: its filesystem
is virtual and in-memory, its generator performs no disk I/O, and
there is no code path from the demo to a real file. Simulation
warnings are on screen at all times (badge + warning strip), and the
demo's own README ([`visual-demo/README.md`](visual-demo/README.md))
states the same guarantee.

## Configuration

`HellHound.py` is configured by constants at the top of the file —
there is no config file and no command-line flag set:

| Constant | Value | Meaning |
|---|---|---|
| `MAX_FILES_LIMIT` | `5000` | Maximum files processed per directory tree |
| `MAX_WORKERS` | `16` | Thread-pool size for file processing |
| `LOG_FREQUENCY` | `50` | Progress is announced every this many files |
| `DELAY_BETWEEN_DELETIONS` | `0.0001` | Pause (seconds) after each file deletion |
| `ENCRYPTION_KEY_FILE` | `hellhound_key.key` | Where the Fernet key is stored (working directory) |
| `REPORT_FILE` | `hellhound_report.json` | Where the JSON run report is written (working directory) |

The visual demo has no configuration file; its runtime controls are
the speed slider and the ransomware-mode checkbox described above.
Its virtual stage set is defined in code (seed `1337`, 256 files, 8
directories).

## Development and testing

The suite ships with a headless test suite (pytest,
`QT_QPA_PLATFORM=offscreen`): **16 tests** — 10 for the visual demo
and 6 for `HellHound.py` — verified by collection from the repository
tree. The demo tests exercise the deterministic virtual filesystem,
build the full UI offscreen, run a complete kill chain to
destruction, verify reset, and confirm the intentional mid-attack
close refusal:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
```

Lint and format are enforced in CI (`ruff` + `black`, line length
100, configured in `pyproject.toml`):

```bash
ruff check visual-demo tests
black --check visual-demo tests
```

CI (`.github/workflows/ci.yml`) runs three jobs on push and pull
request: the headless demo tests, the `ruff` + `black` checks, and a
compile check of the root `HellHound.py`. CodeQL scanning
(`codeql.yml`) runs on push, on pull requests, and weekly. The
Windows executable is built by `build-exe.yml` whenever a release is
published.

## Project layout

```
.
├── HellHound.py               # the real destructive demonstrator (CLI) — see warning above
├── requirements.txt           # cryptography, for HellHound.py
├── visual-demo/
│   ├── hellhound_demo.py      # the visual demo, single file (PyQt5)
│   ├── requirements.txt       # PyQt5, pinned
│   ├── README.md              # demo-focused overview
│   └── assets/
│       ├── hellhound_logo.png # evil dog artwork (header, icon, ransom note)
│       └── hellhound.ico      # Windows exe icon
├── tests/                     # headless pytest suite (visual demo offscreen Qt + HellHound.py)
├── .github/workflows/
│   ├── ci.yml                 # tests + ruff + black + root compile check (push/PR)
│   ├── build-exe.yml          # builds Hellhound.exe on release
│   └── codeql.yml             # CodeQL scanning
├── CHANGELOG.md               # Keep a Changelog; covers both programs
├── SECURITY.md                # how to report vulnerabilities
└── LICENSE                    # Proprietary — all rights reserved
```

## Status

- **`HellHound.py`:** version 2.0, with additional honesty and
  robustness fixes documented as *Unreleased* in the CHANGELOG
  (announced scan failures, announced file-cap hits, corrupt-key
  refusal, truthful cipher naming, reports on failed runs).
- **Visual demo:** version 1.4.0 — the latest release
  (`visual-demo-v1.4`) ships `Hellhound.exe` for Windows.
- Both programs are in active development; the CHANGELOG is the
  record of what changed and when.

## Changelog & security

- [CHANGELOG.md](CHANGELOG.md) — Keep a Changelog format, seeded from
  git history.
- [SECURITY.md](SECURITY.md) — found a vulnerability? Report it
  privately to **Sentinelsafeguard@outlook.com**.

## Contact

Business inquiries: **Sentinelsafeguard@outlook.com** — Skyler
Henderson, Sentinel Safeguard LLC.

## Donations

If this tool earned its keep, BTC is welcome:

```
bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0
```

## License

Proprietary — Copyright (c) 2026 JesusTheHacker / Sentinel Safeguard
LLC. All rights reserved. No copying, redistribution, resale,
republication, or derivative works are permitted without prior
written permission from JesusTheHacker / Sentinel Safeguard LLC. See
[LICENSE](LICENSE) for the full text.

---

*HELLHOUND is an educational tool. In a real attack there is no reset
button: keep offline backups, patch your systems, and have an incident
response plan before you need one.*
