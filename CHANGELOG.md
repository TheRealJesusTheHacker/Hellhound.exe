# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

# Hellhound.exe — visual demo

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

[Unreleased]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/compare/visual-demo-v1.3...main
[1.3.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.3
[1.2.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.2
[1.1.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.1
[1.0.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/releases/tag/visual-demo-v1.0
[2.0.0]: https://github.com/TheRealJesusTheHacker/Hellhound.exe/tree/main
