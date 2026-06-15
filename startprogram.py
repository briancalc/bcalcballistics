# startprogram.py

import subprocess
import sys
import glob
import os

def cleanup_old_files():
    # Remove any existing run files from previous sessions
    patterns = ["trac_run*.json", "term_run*.json", "ballistics_runs.json"]
    removed_count = 0

    for pattern in patterns:
        files = glob.glob(pattern)
        for file_path in files:
            try:
                os.remove(file_path)
                removed_count += 1
                print(f"Removed old file: {file_path}")
            except OSError as e:
                print(f"[ERROR] Could not remove {file_path}: {e}")

    if removed_count > 0:
        print(f"Cleanup complete: {removed_count} old run file(s) removed.")
    else:
        print("No old run files found to remove.")

def run_step(cmd, name):
    print(f"-> Running: {name}")
    result = subprocess.run(cmd)
    rc = result.returncode
    if rc != 0:
        print(f"[WARN] {name} exited with code {rc}")
    return rc

def main():
    # clean up any leftover run files from previous sessions
    cleanup_old_files()

    # Use sys.executable instead of "python3" to ensure venv Python is used
    python = sys.executable

    # run dataentry.py
    run_step([python, "dataentry.py"], "dataentry.py")
    # Check if data was actually stored
    if not os.path.exists("ballistics_runs.json"):
        print("\n[ERROR] No data was stored by dataentry.py. Exiting.")
        sys.exit(1)
    # If we are here, data exists. Proceed.
    print("Data existence verified. Proceeding to next steps...", flush=True)

    # Calculate Ballistics (Direct execution, no subprocess)
    print("-> Calculating Trajectories...")
    try:
        from bdc import calcBDC
        from dataholder2 import get_runs

        runs = get_runs()
        if not runs:
            print("\n[ERROR] No runs found to calculate. Exiting.")
            sys.exit(1)

        for i in range(len(runs)):
            print(f"\n{'='*50}")
            print(f"RUN {i + 1} - Calculating trajectory...")
            print(f"{'='*50}")
            # This generates trac_run{i+1}.json automatically
            calcBDC(800, run_index=i)

        print("\n✓ Trajectory calculations complete.")

    except Exception as e:
        print(f"\n[CRITICAL] Calculation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # run dataformulas.py
    rc_formulas = run_step([python, "dataformulas.py"], "dataformulas.py")
    if rc_formulas != 0:
        print("[WARN] dataformulas.py reported issues; check terminal output above")

    # run dataoutputgui.py
    print("\n-> Launching GUI Display...")
    rc_gui = run_step([python, "dataoutputgui.py"], "dataoutputgui.py")

    #exit with the status of the GUI / last major step
    sys.exit(rc_gui if rc_gui != 0 else rc_formulas)

if __name__ == "__main__":
    main()
