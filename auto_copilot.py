import os
import re
import sys
import time
import glob
import signal
import platform

# Re-exec with the workspace venv if pyautogui is not available in the current interpreter.
_VENV_PYTHON = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "bin", "python")
if os.path.exists(_VENV_PYTHON) and sys.executable != os.path.realpath(_VENV_PYTHON):
    try:
        import pyautogui  # noqa: F401 — just probing
    except ModuleNotFoundError:
        os.execv(_VENV_PYTHON, [_VENV_PYTHON] + sys.argv)

import pyautogui
import pyperclip

# Enable PyAutoGUI Failsafe (Move mouse to top-left corner of screen to abort)
pyautogui.FAILSAFE = True

# Configuration
QUEUE_FILE = "epics_queue.txt"
FAILED_LOG_FILE = "epics_failed.txt"
PROCESSED_LOG_FILE = "epics_processed.txt"
OUTPUT_DIR_TEMPLATE = "uat-test-plans"
MAX_WAIT_SECONDS = 600  # 10 minutes max per Epic
POST_COMPLETION_GRACE_SECONDS = int(os.environ.get("POST_COMPLETION_GRACE_SECONDS", "45"))  # wait for Copilot to finish rendering before /clear
SKIP_IF_EXISTS = os.environ.get("SKIP_IF_EXISTS", "1") != "0"

# Detect OS modifier key for clipboard paste
MODIFIER_KEY = "command" if platform.system() == "Darwin" else "ctrl"

# Global state to track currently processing epic for graceful shutdown
CURRENT_PROCESSING_EPIC = None


def extract_jira_key(epic_ref):
    """Extracts the bare Jira key (e.g. G2-16151) from a full URL or returns the value as-is."""
    match = re.search(r'([A-Z][A-Z0-9]+-\d+)$', epic_ref.strip())
    return match.group(1) if match else epic_ref.strip()


def archive_temp_files(epic_key=None):
    """
    Moves /tmp chunk and payload JSON files into uat-test-plans/source/<EPIC_KEY>/.
    If epic_key is None, archives all UAT artifacts into uat-test-plans/source/startup/.
    """
    if epic_key:
        patterns = [
            f"/tmp/chunk_{epic_key}_*.json",
            f"/tmp/data_payload_{epic_key}.json"
        ]
        dest_dir = os.path.join(OUTPUT_DIR_TEMPLATE, "source", epic_key)
    else:
        patterns = [
            "/tmp/chunk_*.json",
            "/tmp/data_payload_*.json"
        ]
        dest_dir = os.path.join(OUTPUT_DIR_TEMPLATE, "source", "startup")

    archived_count = 0
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.makedirs(dest_dir, exist_ok=True)
                dest = os.path.join(dest_dir, os.path.basename(file_path))
                os.replace(file_path, dest)
                archived_count += 1
            except OSError:
                pass
    return archived_count


def get_remaining_epics(queue_file):
    """Reads all non-empty lines from the queue file."""
    if not os.path.exists(queue_file):
        return []
    with open(queue_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def peek_next_epic(queue_file):
    """Returns the top Epic without removing it; removal happens only after logging."""
    epics = get_remaining_epics(queue_file)
    if not epics:
        return None, 0
    return epics[0], len(epics) - 1


def remove_epic_from_queue(queue_file, epic_key):
    """Removes an Epic from the queue after it has been logged to processed or failed."""
    epics = get_remaining_epics(queue_file)
    updated = [e for e in epics if e != epic_key]
    if len(updated) < len(epics):
        with open(queue_file, "w", encoding="utf-8") as f:
            for epic in updated:
                f.write(f"{epic}\n")



def list_valid_workbooks(epic_key):
    """Returns valid workbook paths and their modified times for an Epic."""
    if not os.path.exists(OUTPUT_DIR_TEMPLATE):
        return {}

    xlsx_files = [
        f for f in glob.glob(os.path.join(OUTPUT_DIR_TEMPLATE, f"{epic_key}-*.xlsx"))
        if not os.path.basename(f).startswith("~$")
    ]
    workbooks = {}
    for path in xlsx_files:
        try:
            workbooks[path] = os.path.getmtime(path)
        except OSError:
            pass
    return workbooks


def epic_has_existing_output(epic_key):
    """Returns True when the Epic already has at least one non-temp XLSX output."""
    return bool(list_valid_workbooks(epic_key))


def is_workbook_generated(epic_key, run_start_time, baseline_workbooks):
    """
    Checks if a valid workbook has been created or updated after this run started.
    Ignores temporary Excel lock files (starting with ~$).
    """
    current_workbooks = list_valid_workbooks(epic_key)
    if not current_workbooks:
        return False

    # Success when a new workbook appears or an existing one is updated after start.
    for path, modified_time in current_workbooks.items():
        baseline_modified_time = baseline_workbooks.get(path)
        if baseline_modified_time is None:
            return True
        if modified_time > max(run_start_time, baseline_modified_time):
            return True
    return False


def log_processed(epic_key, elapsed_seconds, note=None):
    """Logs completed or intentionally skipped Epics to epics_processed.txt."""
    with open(PROCESSED_LOG_FILE, "a", encoding="utf-8") as f:
        status_suffix = f" | {note}" if note else ""
        f.write(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {epic_key} "
            f"(Completed in {elapsed_seconds}s){status_suffix}\n"
        )


def log_failure(epic_key, reason):
    """Logs stalled or timed-out Epics to epics_failed.txt for manual review."""
    with open(FAILED_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {epic_key}: {reason}\n")


def send_to_copilot(text):
    """Pastes text via system clipboard to avoid pyautogui typing corruption."""
    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey(MODIFIER_KEY, "v")
    time.sleep(0.2)
    pyautogui.press("enter")


def clear_chat_context():
    """Attempts to clear Copilot chat context without crashing the loop."""
    try:
        time.sleep(3)
        print(" Clearing chat context window...")
        send_to_copilot("/clear")
    except pyautogui.FailSafeException:
        print(" [WARN] Failsafe triggered while attempting /clear.")
    except Exception as e:
        print(f" [WARN] Failed to send /clear: {e}")


def handle_shutdown(sig, frame):
    """Graceful interrupt handler — epic stays in queue since it was never removed."""
    print("\n\n[WARNING] Process interrupted by user!")
    if CURRENT_PROCESSING_EPIC:
        archive_temp_files(extract_jira_key(CURRENT_PROCESSING_EPIC))
    sys.exit(0)


# Register Ctrl+C signal handler
signal.signal(signal.SIGINT, handle_shutdown)


def main():
    global CURRENT_PROCESSING_EPIC

    print("=" * 60)
    print("   UAT COPILOT BATCH PROCESSOR (HARDENED LOOP)   ")
    print("=" * 60)
    print("Instructions:")
    print("1. Open VS Code with Copilot Chat ready.")
    print("2. Focus the Copilot chat input box.")
    print("3. Move mouse to top-left corner at ANY time to abort.")
    print("=" * 60)

    # Startup Cleanup: Archive any stale payload/chunk files from previous runs
    initial_archived = archive_temp_files()
    if initial_archived > 0:
        print(f"🧹 Pre-flight Cleanup: Archived {initial_archived} stale temporary file(s) to uat-test-plans/source/startup/.")

    for i in range(5, 0, -1):
        print(f" Starting in {i} seconds... (Switch to VS Code now)")
        time.sleep(1)

    while True:
        try:
            # 1. Peek at top Epic without removing it from the queue yet
            epic_key, remaining_count = peek_next_epic(QUEUE_FILE)
            if not epic_key:
                print("\n Queue is empty! All Epics processed.")
                break

            CURRENT_PROCESSING_EPIC = epic_key
            # bare_key is used for file paths; epic_key (may be a URL) goes into the prompt
            bare_key = extract_jira_key(epic_key)
            print(f"\n Processing Epic: {bare_key} ({remaining_count} remaining in queue)")

            # Archive any old temp files for this specific Epic key before starting
            archive_temp_files(bare_key)

            # Optional hard guard: skip epics that already produced output.
            if SKIP_IF_EXISTS and epic_has_existing_output(bare_key):
                print(f" Skipping {bare_key}: existing workbook already found in output folder.")
                log_processed(bare_key, 0, "SKIPPED: existing workbook")
                remove_epic_from_queue(QUEUE_FILE, epic_key)
                CURRENT_PROCESSING_EPIC = None
                clear_chat_context()
                continue

            # 2. Formulate explicit prompt
            prompt = f"Run .github/prompts/uat-test-plan-template.md for Epic '{epic_key}' and generate /tmp/data_payload_{bare_key}.json before executing the Python generator script."

            baseline_workbooks = list_valid_workbooks(bare_key)

            # 3. Paste prompt and execute
            print(f" Sending prompt to Copilot for {bare_key}...")
            send_to_copilot(prompt)

            # 4. Poll file system until .xlsx file is created
            start_time = time.time()
            completed = False

            while (time.time() - start_time) < MAX_WAIT_SECONDS:
                if is_workbook_generated(bare_key, start_time, baseline_workbooks):
                    elapsed = int(time.time() - start_time)
                    print(f" Success! Excel workbook detected for {bare_key} ({elapsed}s elapsed).")
                    print(f" Waiting {POST_COMPLETION_GRACE_SECONDS}s for Copilot to finish rendering before /clear...")
                    time.sleep(POST_COMPLETION_GRACE_SECONDS)
                    log_processed(bare_key, elapsed)
                    remove_epic_from_queue(QUEUE_FILE, epic_key)
                    completed = True
                    break

                time.sleep(3)

            # Handle Timeout Failsafe
            if not completed:
                print(f" ERROR: Timeout ({MAX_WAIT_SECONDS}s) reached for {bare_key}. Logging to epics_failed.txt...")
                log_failure(bare_key, f"Timed out after {MAX_WAIT_SECONDS}s without producing XLSX")
                remove_epic_from_queue(QUEUE_FILE, epic_key)

            # Post-Epic Cleanup: Archive temporary files generated for this Epic
            archive_temp_files(bare_key)

            # 5. Clear context window
            clear_chat_context()

            # Reset tracking variable
            CURRENT_PROCESSING_EPIC = None

            # Short pause before starting next iteration
            time.sleep(2)

        except pyautogui.FailSafeException:
            print("\n\n[FAILSAFE] PyAutoGUI failsafe triggered (Mouse in top-left corner)!")
            if CURRENT_PROCESSING_EPIC:
                # Epic was never removed from queue, so it will retry on next run
                archive_temp_files(extract_jira_key(CURRENT_PROCESSING_EPIC))
            clear_chat_context()
            break
        except Exception as e:
            print(f"\n[ERROR] Unexpected loop crash: {e}")
            if CURRENT_PROCESSING_EPIC:
                # Epic was never removed from queue, so it will retry on next run
                archive_temp_files(extract_jira_key(CURRENT_PROCESSING_EPIC))
            clear_chat_context()
            break


if __name__ == "__main__":
    main()