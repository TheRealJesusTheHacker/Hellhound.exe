# HELLHOUND Visual Demo

A scary-looking **educational simulation** of how a deletion virus works,
built for live demonstration shows.

## What it is

A PyQt5 app that walks an audience through a malware kill chain on a
**fully virtual filesystem** (256 fake files, ~1 GB of fake data):

1. **Infiltration** -- payload lands, persistence established
2. **Reconnaissance** -- filesystem surveyed, targets prioritized
3. **Encryption** -- ransomware mode: files "encrypted" (optional toggle)
4. **Deletion** -- wiper phase, shadow copies purged
5. **Ransom note** -- payoff demand with a 72-hour countdown timer

Every phase narrates **what you're seeing** and **how to stop it** (defense
tips), with a live terminal-style attack log, file tree that marks files
FOUND → ENCRYPTED → DELETED (struck through in red), live stats (files
deleted, files encrypted, data destroyed, deletion rate), speed control (1–30x), and
reset.

## No escape

Like the real thing, there is no shutting it down once launched: no pause
button, Reset is disabled mid-attack, and even the window close button
refuses until destruction is complete ("You can't close HellHound. It
finishes what it started."). It runs until every virtual file is gone.

## Safety

**Simulation only.** No real files are read, written, encrypted, or deleted.
Nothing on the host machine is touched, ever. The destruction is real
*within the simulation* -- every virtual file is genuinely encrypted and
deleted in the sim -- but it cannot reach real files. A yellow
⚠ SIMULATION ⚠ badge and warning strips say so throughout.

## Run it

```bash
pip install -r requirements.txt
python hellhound_demo.py
```

Press **🔥 LAUNCH ATTACK**. Drag the speed slider for slow dramatic
walkthroughs (1x) or full runs in seconds (30x).

## Files

- `hellhound_demo.py` -- the whole app, single file
- `assets/hellhound_logo.png` -- the evil dog artwork (header, ransom note, window icon)
- `assets/hellhound.ico` -- Windows icon for the built Hellhound.exe

## License

MIT — this demo is covered by the repository's [LICENSE](../LICENSE).
