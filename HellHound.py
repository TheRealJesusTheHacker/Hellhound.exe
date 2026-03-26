import os
import sys
import shutil
import time

def display_hellhound_message():
    """Display HellHound message instead of normal boot messages"""
    print("\033[91mCyberdogs HellHound has been released. He was hungry for your computers soul. All data has been destroyed.\033[0m")
    # Additional visual effects
    print("\n" + "="*50)
    print("         ⚠️  CYBER DOGS ALERT  ⚠️")
    print("="*50)
    print("\n💀 YOUR SYSTEM IS NOW INFECTED 💀")
    print("🧠 HELLHOUND IS CONSUMING RESOURCES 🧠")
    print("💾 ALL DATA DESTROYED IN 3 SECONDS 💾")
    print("\n" + "="*50)

def main():
    # First display the HellHound message
    display_hellhound_message()
    
    # Then proceed with destructive operations
    print("\nExecuting HellHound payload...")
    
    # Delete the OS (simplified version)
    print("[+] Deleting root filesystem...")
    try:
        # Simulate deletion without actually deleting
        print("[+] Root filesystem marked for deletion")
    except Exception as e:
        print(f"[!] Error: {e}")
    
    # Delete all files
    print("[+] Starting file deletion process...")
    deleted_count = 0
    try:
        for root, dirs, files in os.walk('/'):
            for file in files:
                try:
                    # Simulate deletion without actually deleting
                    deleted_count += 1
                    if deleted_count % 1000 == 0:
                        print(f"[+] Deleted {deleted_count} files...")
                except Exception:
                    continue
                    
        print(f"[+] Completed deletion of {deleted_count} files")
    except Exception as e:
        print(f"[!] Error during file deletion: {e}")
    
    print("\n[!] HellHound payload execution complete!")
    print("[!] Your system is now compromised!")

if __name__ == "__main__":
    main()
