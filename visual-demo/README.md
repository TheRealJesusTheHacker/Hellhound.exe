# HELLHOUND Visual Demo

A scary-looking **educational simulation** of how a deletion virus
works, built for live demonstration shows.

> **Scope note:** this README covers only the visual demo in this
> directory. The repository root contains a second, separate program,
> `HellHound.py`, which performs **real** file encryption and deletion
> on the machine it runs on. That tool is documented — with its
> warning and consent flow — in the [root README](../README.md). The
> demo below never touches real files; the root tool does. Do not
> confuse them.

## What it is

A PyQt5 app that walks an audience through a malware kill chain on a
**fully virtual filesystem** (256 fake files, ~1 GB of fake data,
generated deterministically from seed `1337` across 8 fake
directories):

1. **Infiltration** — payload lands, persistence established
2. **Reconnaissance** — filesystem surveyed, targets prioritized
3. **Encryption** — ransomware mode: files "encrypted" (optional
   toggle; simulated — no real cryptography is performed)
4. **Deletion** — wiper phase, shadow copies purged
5. **Ransom note** — payoff demand with a 72-hour countdown timer and
   a fake demonstration address (do not pay)

Every phase narrates **what you're seeing** and **how to stop it**
(defense tips), with a live terminal-style attack log, a file tree
that marks files FOUND → ENCRYPTED → DELETED (struck through in red),
live stats (files deleted, files encrypted, data destroyed, deletion
rate), a speed control (1–30×, default 5×), a ransomware-mode
checkbox, and reset.

## No escape

Like the real thing, there is no shutting it down once launched: no
pause button, Launch / Reset / the ransomware-mode toggle are disabled
while an attack is running, and even the window close button refuses
until destruction is complete ("You can't close HellHound. It finishes
what it started."). It runs until every virtual file is gone. This
theatrical behavior is intentional and covered by tests.

## Safety

**Simulation only.** No real files are read, written, encrypted, or
deleted. Nothing on the host machine is touched, ever. The filesystem
is virtual and lives entirely in memory; the generator performs no
disk I/O. The destruction is real *within the simulation* — every
virtual file is genuinely marked encrypted and deleted in the sim —
but it cannot reach real files. A yellow ⚠ SIMULATION ⚠ badge and
warning strips say so throughout the app.

## Run it

From this directory:

```bash
pip install -r requirements.txt
python hellhound_demo.py
```

Or from the repository root:

```bash
pip install -r visual-demo/requirements.txt
python visual-demo/hellhound_demo.py
```

Requires Python 3.7+ and PyQt5 (pinned in `requirements.txt`).

Press **🔥 LAUNCH ATTACK**. Drag the speed slider for slow dramatic
walkthroughs (1×) or full runs in seconds (30×).

### Windows build

`Hellhound.exe` — this demo, built with PyInstaller — is attached to
every release on the repository's Releases page, with a signed
build-provenance attestation.

## Tests

The headless suite in [`../tests/`](../tests/) covers this demo:
the deterministic virtual filesystem, the offscreen UI build, a full
kill-chain run to completion, reset, and the intentional mid-attack
close refusal.

```bash
# from the repository root
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
```

## Files

- `hellhound_demo.py` — the whole app, single file
- `assets/hellhound_logo.png` — the evil dog artwork (header, ransom
  note, window icon)
- `assets/hellhound.ico` — Windows icon for the built Hellhound.exe

## License

Proprietary — this demo is covered by the repository's
[LICENSE](../LICENSE). Copyright (c) 2026 JesusTheHacker / Sentinel
Safeguard LLC. All rights reserved.
