# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

# Hellhound.exe — visual demo

## [1.4.0] - 2026-10-25

### Changed
- Release of the current `main` state. The visual demo's behavior is
  unchanged from 1.3.0; what this release ships on top of it is the
  repository work since then, in plain terms:
  - Sweep #5 fix in the root `HellHound.py` tool (see the
    HellHound [Unreleased] entries below, which this release carries):
    `encrypt_file` now refuses symlinks by the same `lstat` rule the
    worker uses, so a path swapped for a symlink mid-run can no longer
    cause a file outside the announced target trees to be encrypted in
    place; the generated encryption key file is created owner-only
    (0o600); a scan restarted after Ctrl+C no longer double-counts
    scan errors.
  - Dependency installs are hash-locked: every install path (CI, the
    release build, and the documented from-source installs) runs
    `pip install --require-hashes` against committed lock files, so a
    mismatched artifact fails the install loudly.
  - A functional pass over both programs (headless demo runs with
    ransomware mode on and off, and the root tool's consent/scope
    flow exercised against a scratch directory only) found no
    defects. Suite: 19 passed.

## [1.3.0] - 2026-10-11

### Added
- Headless test suite (`tests/`, pytest, `QT_QPA_PLATFORM=offscreen`) covering
  the deterministic virtual filesystem, offscreen UI build, full kill-chain
  run to completion, reset, and the intentional mid-attack close refusal.
- `ci.yml` workflow: headless tests plus `ruff` and `black` checks on every
  push and pull request (SHA-pinned actions).
- Issue templates (bug report, feature request) and a pull-request template
  with a simulation-only scope checklist.
- `pyproject.toml` with `ruff`/`black` configuration.

### Fixed
- Attack stats now shown in the ransom dialog (previously computed but never
  displayed); stale GUI signal-count comment corrected.
- README no longer claims a pause control that does not exist.

### Changed
- `build-exe.yml`: checkout no longer persists the git token
  (`persist-credentials: false`) — the release build job needs only the API
  token (release upload + build provenance attestation).

## [1.2.0] - 2026-10-10

### Added
- Build provenance attestation on the released `Hellhound.exe` artifact.
- Dependabot (pip + GitHub Actions, weekly) and CodeQL scanning on push, PR,
  and a weekly schedule.

### Changed
- Pinned `pyinstaller`, `PyQt5`, and GitHub Actions to exact versions/SHAs.
- Reset no longer blocks the GUI thread — the engine is stopped via its
  `finished` signal.
- Stop flag is now a `threading.Event` (was a shared plain bool).

### Fixed
- Batched GUI signal delivery: ~1,280 per-run signal deliveries down to
  ~12/11/11 per phase at 30× speed; stats repaints throttled to ~10 Hz.
- `QBrush`/`QFont` cached per file status instead of constructed per event.

## [1.1.0] - 2026-09-20

### Added
- Hellhound's sign-off in blood-red terminal text at total destruction:
  "Hellhound Fetched Their souls. Hard drives will Rott in Hell. Goodbye My Pup."

### Changed
- Repo renamed to Hellhound.exe; README rebranded around the visual demo.

## [1.0.0] - 2026-09-20

### Added
- First release of the HELLHOUND visual demo as `Hellhound.exe`
  (Windows, PyInstaller).
- 256 virtual files across 8 fake system directories, 5 kill-chain phases
  (infiltration, reconnaissance, encryption, deletion, ransom note).
- Live terminal log, phase tracker, defense tips, kill stats, 1–30× speed
  control, ransomware-mode toggle.
- No-escape mode: no pause button, Reset/Launch disabled mid-attack, window
  refuses to close until destruction is complete.
- Simulation only: no real files ever read, encrypted, or deleted.

---

# HellHound Malware — educational tool

## [Unreleased]

### Fixed
- Sweep #5, 2026-10-24 (bug hunt + performance): `encrypt_file` now
  gates on `lstat` like the worker does — with `stat` (follow) a path
  swapped for a symlink between the worker's check and encryption
  would have encrypted the symlink's target, a file outside the
  announced target trees, in place. Symlinks are refused and their
  targets are never written. The generated encryption key file is now
  created owner-only (0o600) instead of inheriting the umask. A scan
  restarted after Ctrl+C no longer double-counts scan errors in the
  final summary. Removed the vestigial per-file deletion delay
  (measured on a 2,000-file synthetic tree: ~1.16 s → ~0.37–0.58 s).
  Regression tests for all four in `tests/test_hellhound.py`.
- Sweep #3, 2026-10-21 (education-tool lens — warnings / consent /
  announced scope / no silent actions): a Ctrl+C landing *between*
  trees in `delete_system_files` — outside the worker's scan /
  processing / cleanup phases, the only places that disregard it —
  escaped to `main()`'s interrupt handler and stopped the run
  mid-scope, contradicting the in-run "does not stop mid-run"
  announcements. The interrupted tree is now re-processed (idempotent)
  and the run completes its announced scope; regression test in
  `tests/test_hellhound.py`.
- `encrypt_file` catches `MemoryError` alongside `Exception`: the explicit
  name documents the case that matters — a file larger than available RAM
  raises it in `f.read()`. (Correction: `MemoryError` is a subclass of
  `Exception`, so the previous `except Exception` handler already caught
  it; this entry originally misdescribed it as an escaping BaseException.)
  The file is skipped and counted in `stats["errors"]`; data-safe
  (encryption fails before any write/remove).
- `delete_system_files` now sets `stats["end_time"]` on the
  no-target-directories early return, so the execution summary and JSON
  report no longer show a null end time on that path.
- Removed unused imports (`shutil`, `glob`, `pathlib.Path`) from
  `HellHound.py`.
- `main()` announces the exact target directories before the 'YES'
  confirmation prompt, so consent is given against the real scope instead
  of each directory being named only as its processing begins.
- `load_encryption_key` validates a stored key with `Fernet(key)` instead of
  crashing on a corrupt `hellhound_key.key`: the key file is NOT overwritten,
  the user is told to delete it to generate a fresh one, and encryption mode
  refuses cleanly without touching any files.
- Directory scans no longer fail silently. `os.walk` swallows `scandir`
  errors by default, so an unreadable directory, an over-long path
  (> PATH_MAX), or a directory vanishing mid-scan was skipped with no
  message and no error count — while the run still reported "Directory
  complete" and "Errors Encountered: 0". Scan failures are now announced
  as they happen (naming the path and that its contents were NOT
  processed) and counted in `stats["errors"]`.
- Reaching the per-tree file limit (`MAX_FILES_LIMIT`) is announced
  before processing starts, naming the limit and that remaining files
  were NOT processed. Previously a tree larger than the limit was
  truncated in silence and still reported as complete.
- A failed JSON report write (full disk, read-only working directory)
  no longer turns a completed run into a "Fatal error" exit — the
  failure is announced and the run's own verdict stands.
- Ctrl+C during a run no longer stops it: the processing loop's
  interrupt handler cancelled every queued file and abandoned the
  rest of the announced scope. Interrupts during a run (scan,
  processing, directory cleanup) are now announced and disregarded,
  so a started run completes its announced scope — matching the
  documented design. Ctrl+C is honored only at the prompts before a
  run starts; ending a started run means ending the process.

### Changed
- Performance pass on the deletion engine (no behavior or signature
  changes; verified by before/after benchmarks on synthetic trees plus
  parity harnesses):
  - The per-file acceptance check is a single `lstat` instead of three
    stat calls (`isfile` + `islink` + `getsize`); `encrypt_file` likewise
    uses one `stat` instead of `isfile()` + `getsize()`. The set of files
    accepted/skipped — symlinks never followed or deleted — is unchanged.
  - Futures are submitted in a bounded window (`MAX_WORKERS * 4`) instead
    of one per file up front: peak memory on a 25,000-file run dropped
    from ~78 MB to ~26 MB. Progress announcements and totals are unchanged.
  - Thread pool widened 8 → 16 workers (deletion is I/O-latency-bound;
    ~40% faster on the benchmark tree, 32 workers was no better).
  - Empty-directory cleanup attempts `rmdir` directly instead of listing
    every directory first (rmdir only succeeds when empty).
  - Net effect on the benchmark trees: 5,000-file delete ~2.6 s → ~1.1 s;
    25,000-file delete ~7.4 s → ~3.5 s; encrypt+delete of 1,000 × 64 KiB
    files ~4.3 s → ~2.9 s.

## [2.0.0] - 2026-07-04

### Added
- Multi-threading architecture: `ThreadPoolExecutor` with 8 parallel worker
  threads, thread-safe statistics collection, 10–50× speed improvement over
  single-threaded (typical 50–200+ files/second).
- Encryption module (Fernet/AES-128-CBC): automatic key generation stored in
  `hellhound_key.key`; encrypts files before deletion (ransomware simulation).
- Dual operation modes: deletion-only or encryption + deletion, selectable at
  runtime.
- JSON report generation (`hellhound_report.json`) with timestamps, counts,
  data volume, performance metrics, error tracking, and educational metadata.
- Real-time deletion rate, execution time tracking, and human-readable data
  volume statistics.

### Changed
- `DELAY_BETWEEN_DELETIONS` reduced from 0.001 to 0.0001 seconds.
- Optimized file discovery with pre-collection before threading; improved
  error handling and graceful interrupt handling with JSON report on exit.
- README overhauled with threading architecture diagram, encryption flow,
  performance benchmarks, report structure examples, and troubleshooting.
- `requirements.txt`: added `cryptography>=41.0.0` dependency.

### Fixed
- Race conditions in statistics updates, permission-error handling during
  parallel operations, thread-safe file size calculation, correct aggregation
  of multiple directory results.

## [1.0.0] - 2026-04-02

### Added
- Cross-platform file deletion (Windows: Temp/Downloads/Desktop/Recent;
  Linux/macOS: /tmp, .cache, Trash) with real-time colored visual logging.
- Explicit user confirmation ("YES"), `MAX_FILES_LIMIT` (5000), configurable
  delay between deletions, graceful error handling.
- Execution summary: files deleted count, directories removed, platform info,
  execution timestamp.
- Full educational documentation: features, installation, usage, target
  directories, security implications, mitigation strategies, references.

---

[Unreleased]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/compare/visual-demo-v1.4...main
[1.4.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.4
[1.3.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.3
[1.2.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.2
[1.1.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.1
[1.0.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.0
[2.0.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/tree/main
