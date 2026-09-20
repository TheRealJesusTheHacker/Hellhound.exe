# Hellhound.exe

The scary one. A blood-red PyQt5 visual simulation of a ransomware kill chain —
**infiltration → recon → encryption → deletion → ransom note** — played out
against 256 virtual files in an in-memory filesystem.

**It never touches real files.** Nothing on the host is read, encrypted, or
deleted. This is an educational stage, not a weapon.

## Download

Grab **Hellhound.exe** from the
[Releases page](https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases).
Windows build, packaged automatically with PyInstaller.

## What it does

- 256 virtual files (~1 GB) across fake system directories
- Live terminal log, phase tracker, defense tips, kill stats
- 1–30x speed control
- **No escape:** no pause button, Reset/Launch die mid-attack, and the window
  refuses to close until total destruction. It finishes what it started.
- Ends with a fake 72-hour ransom countdown and Hellhound's sign-off in red:
  *"Hellhound Fetched Their souls. Hard drives will Rott in Hell. Goodbye My Pup."*

## Run from source

```bash
pip install -r visual-demo/requirements.txt
python visual-demo/hellhound_demo.py
```

## Also in this repo

- `HellHound.py` — the original terminal-based educational tool (v2.0). Unlike
  the visual demo, it performs **real** file deletion/encryption: controlled
  environments only, explicit permission required.
- `visual-demo/` — source for Hellhound.exe (simulation only).

## Disclaimer

Educational purposes only. The authors assume no liability for misuse.
