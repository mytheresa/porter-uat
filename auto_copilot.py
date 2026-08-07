import os
import re
import sys
import time
import glob
import random
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
ARTIFACTS_DIR = os.path.join(OUTPUT_DIR_TEMPLATE, "source")
MAX_WAIT_SECONDS = 600  # 10 minutes max per Epic
POST_COMPLETION_GRACE_SECONDS = int(os.environ.get("POST_COMPLETION_GRACE_SECONDS", "30"))  # wait for Copilot to finish rendering before /clear
SKIP_IF_EXISTS = os.environ.get("SKIP_IF_EXISTS", "1") != "0"
PERSIST_JSON_ARTIFACTS = os.environ.get("PERSIST_JSON_ARTIFACTS", "1") != "0"
PERSIST_CHUNK_ARTIFACTS = os.environ.get("PERSIST_CHUNK_ARTIFACTS", "0") != "0"
SEND_RETRIES = int(os.environ.get("SEND_RETRIES", "3"))
RATE_LIMIT_RETRY_MAX = int(os.environ.get("RATE_LIMIT_RETRY_MAX", "2"))
RATE_LIMIT_RETRY_BASE_SECONDS = int(os.environ.get("RATE_LIMIT_RETRY_BASE_SECONDS", "5"))
RATE_LIMIT_RETRY_CAP_SECONDS = int(os.environ.get("RATE_LIMIT_RETRY_CAP_SECONDS", "180"))

# Detect OS modifier key for clipboard paste
MODIFIER_KEY = "command" if platform.system() == "Darwin" else "ctrl"

# Global state to track currently processing epic for graceful shutdown
CURRENT_PROCESSING_EPIC = None
EPIC_SORT_PATTERN = re.compile(r'^([A-Z][A-Z0-9]*)-(\d+)$')


def epic_sort_key(epic_key):
    key = str(epic_key or "").strip()
    match = EPIC_SORT_PATTERN.match(key)
    if match:
        return match.group(1), int(match.group(2)), key
    return "~", 10**12, key


def extract_epic_from_log_line(line):
    match = re.search(r'\b([A-Z][A-Z0-9]*-\d+)\b', line or "")
    return match.group(1) if match else ""


def upsert_sorted_log_line(log_path, epic_key, new_line):
    lines = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.readlines() if extract_epic_from_log_line(ln) != epic_key]

    lines.append(new_line)
    lines.sort(key=lambda ln: epic_sort_key(extract_epic_from_log_line(ln)))

    with open(log_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def extract_jira_key(epic_ref):
    """Extracts the bare Jira key (e.g. G2-16151) from a full URL or returns the value as-is."""
    match = re.search(r'([A-Z][A-Z0-9]+-\d+)$', epic_ref.strip())
    return match.group(1) if match else epic_ref.strip()


def cleanup_temp_files(epic_key=None):
    """
    Handles /tmp chunk and payload JSON files.
    Payload files can be persisted for re-generation; chunk files are temp-only by default.
    If epic_key is None, applies to all UAT temp artifacts.
    """
    if epic_key:
        patterns = [
            f"/tmp/chunk_{epic_key}_*.json",
            f"/tmp/data_payload_{epic_key}.json"
        ]
    else:
        patterns = [
            "/tmp/chunk_*.json",
            "/tmp/data_payload_*.json"
        ]

    handled_count = 0
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            file_name = os.path.basename(file_path)
            is_chunk = file_name.startswith("chunk_")
            should_persist = PERSIST_JSON_ARTIFACTS and (not is_chunk or PERSIST_CHUNK_ARTIFACTS)
            try:
                if should_persist:
                    target_epic = epic_key
                    if not target_epic:
                        match = re.search(r'(?:^data_payload_|^chunk_)([A-Z][A-Z0-9]+-\d+)', file_name)
                        target_epic = match.group(1) if match else None

                    # Unknown-key leftovers are deleted to avoid creating a generic startup bucket.
                    if not target_epic:
                        os.remove(file_path)
                    else:
                        persist_dir = os.path.join(ARTIFACTS_DIR, target_epic)
                        os.makedirs(persist_dir, exist_ok=True)
                        destination = os.path.join(persist_dir, file_name)
                        os.replace(file_path, destination)
                else:
                    os.remove(file_path)
                handled_count += 1
            except OSError:
                pass
    return handled_count


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
    status_suffix = f" | {note}" if note else ""
    line = (
        f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {epic_key} "
        f"(Completed in {elapsed_seconds}s){status_suffix}\n"
    )
    upsert_sorted_log_line(PROCESSED_LOG_FILE, epic_key, line)


def log_failure(epic_key, reason):
    """Logs stalled or timed-out Epics to epics_failed.txt for manual review."""
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {epic_key}: {reason}\n"
    upsert_sorted_log_line(FAILED_LOG_FILE, epic_key, line)


def detect_secondary_rate_limit(epic_key, since_epoch=None):
    """
    Detects GitHub secondary rate-limit errors emitted into the generated payload.
    Returns: (detected, retry_after_seconds, source_path)
    """
    candidate_paths = [
        f"/tmp/data_payload_{epic_key}.json",
        os.path.join(ARTIFACTS_DIR, epic_key, f"data_payload_{epic_key}.json"),
    ]

    for path in candidate_paths:
        if not os.path.exists(path):
            continue

        if since_epoch is not None:
            try:
                if os.path.getmtime(path) < since_epoch:
                    continue
            except OSError:
                continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        if "secondary rate limit exceeded" not in content.lower():
            continue

        retry_after_match = re.search(r"retry after\s*(\d+)s", content, flags=re.IGNORECASE)
        retry_after_seconds = int(retry_after_match.group(1)) if retry_after_match else 45
        return True, retry_after_seconds, path

    return False, None, None


def compute_rate_limit_retry_delay(retry_after_seconds, attempt_number):
    """Computes cooldown with exponential backoff and small jitter."""
    exponential_backoff = RATE_LIMIT_RETRY_BASE_SECONDS * (2 ** max(0, attempt_number - 1))
    jitter = random.randint(0, 5)
    return min(retry_after_seconds + exponential_backoff + jitter, RATE_LIMIT_RETRY_CAP_SECONDS)


def send_to_copilot(text):
    """Paste and verify text before submit to avoid partial sends (e.g. lone 'v')."""
    expected = text.strip()
    original_clipboard = None
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        # Clipboard read failures should not block prompt sending.
        pass

    sent = False
    for attempt in range(1, SEND_RETRIES + 1):
        pyperclip.copy(text)
        time.sleep(0.3)  # allow focus to settle before pasting
        pyautogui.hotkey(MODIFIER_KEY, "a")
        time.sleep(0.1)
        pyautogui.hotkey(MODIFIER_KEY, "v")
        time.sleep(0.2)

        # Verify what is in the input before pressing Enter.
        pyautogui.hotkey(MODIFIER_KEY, "a")
        time.sleep(0.1)
        pyautogui.hotkey(MODIFIER_KEY, "c")
        time.sleep(0.1)
        observed = pyperclip.paste().strip()
        if observed == expected:
            pyautogui.press("enter")
            sent = True
            break

        print(f" [WARN] Prompt verification failed on attempt {attempt}/{SEND_RETRIES}.")
        time.sleep(0.2)

    if original_clipboard is not None:
        try:
            pyperclip.copy(original_clipboard)
        except Exception:
            pass

    return sent


def clear_chat_context():
    """Attempts to clear Copilot chat context without crashing the loop."""
    try:
        time.sleep(5)  # give VS Code time to re-focus the chat input after workbook generation
        print(" Clearing chat context window...")
        if not send_to_copilot("/clear"):
            print(" [WARN] Could not verify /clear command before submit.")
    except pyautogui.FailSafeException:
        print(" [WARN] Failsafe triggered while attempting /clear.")
    except Exception as e:
        print(f" [WARN] Failed to send /clear: {e}")


def handle_shutdown(sig, frame):
    """Graceful interrupt handler — epic stays in queue since it was never removed."""
    print("\n\n[WARNING] Process interrupted by user!")
    if CURRENT_PROCESSING_EPIC:
        cleanup_temp_files(extract_jira_key(CURRENT_PROCESSING_EPIC))
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

    # Startup Cleanup: Persist/remove stale payload/chunk files from previous runs
    initial_archived = cleanup_temp_files()
    if initial_archived > 0:
        action = "Persisted/cleaned" if PERSIST_JSON_ARTIFACTS else "Removed"
        print(f"🧹 Pre-flight Cleanup: {action} {initial_archived} stale temporary file(s).")

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

            # Remove any old temp files for this specific Epic key before starting
            cleanup_temp_files(bare_key)

            # Optional hard guard: skip epics that already produced output.
            if SKIP_IF_EXISTS and epic_has_existing_output(bare_key):
                print(f" Skipping {bare_key}: existing workbook already found in output folder.")
                log_processed(bare_key, 0, "SKIPPED: existing workbook")
                remove_epic_from_queue(QUEUE_FILE, epic_key)
                CURRENT_PROCESSING_EPIC = None
                clear_chat_context()
                continue

            # 2. Formulate explicit prompt
            prompt = (
                f"Read .github/prompts/uat-test-plan-template.md and strictly follow the Mandatory Orchestration Workflow for Epic {bare_key}. "
                f"Create /tmp/data_payload_{bare_key}.json. "
                f"Validate then generate with .github/scripts/generate-test-plan-xlsx.py using /tmp/data_payload_{bare_key}.json. "
                "Batch mode: do not render final chat output."
            )

            completed = False
            attempt = 1
            max_attempts = RATE_LIMIT_RETRY_MAX + 1
            while attempt <= max_attempts:
                baseline_workbooks = list_valid_workbooks(bare_key)

                # 3. Paste prompt and execute
                print(f" Sending prompt to Copilot for {bare_key} (attempt {attempt}/{max_attempts})...")
                if not send_to_copilot(prompt):
                    print(f" ERROR: Could not reliably send prompt for {bare_key}.")
                    log_failure(bare_key, "Prompt send verification failed")
                    remove_epic_from_queue(QUEUE_FILE, epic_key)
                    cleanup_temp_files(bare_key)
                    clear_chat_context()
                    CURRENT_PROCESSING_EPIC = None
                    time.sleep(2)
                    break

                # 4. Poll file system until .xlsx file is created
                start_time = time.time()
                retry_scheduled = False
                while (time.time() - start_time) < MAX_WAIT_SECONDS:
                    # Detect known rate-limit failures as soon as they are written to payload artifacts.
                    rate_limited, retry_after_seconds, source_path = detect_secondary_rate_limit(
                        bare_key,
                        since_epoch=start_time,
                    )
                    if rate_limited and attempt < max_attempts:
                        retry_delay = compute_rate_limit_retry_delay(retry_after_seconds, attempt)
                        print(
                            f" [WARN] Secondary rate limit detected in {source_path}. "
                            f"Retrying {bare_key} after {retry_delay}s cooldown..."
                        )
                        cleanup_temp_files(bare_key)
                        clear_chat_context()
                        time.sleep(retry_delay)
                        attempt += 1
                        retry_scheduled = True
                        break

                    if is_workbook_generated(bare_key, start_time, baseline_workbooks):
                        elapsed = int(time.time() - start_time)
                        print(f" Success! Excel workbook detected for {bare_key} ({elapsed}s elapsed).")
                        print(f" Waiting {POST_COMPLETION_GRACE_SECONDS}s for Copilot to finish rendering before /clear...")
                        time.sleep(POST_COMPLETION_GRACE_SECONDS)

                        rate_limited, retry_after_seconds, source_path = detect_secondary_rate_limit(
                            bare_key,
                            since_epoch=start_time,
                        )
                        if rate_limited and attempt < max_attempts:
                            retry_delay = compute_rate_limit_retry_delay(retry_after_seconds, attempt)
                            print(
                                f" [WARN] Secondary rate limit detected in {source_path}. "
                                f"Retrying {bare_key} after {retry_delay}s cooldown..."
                            )
                            cleanup_temp_files(bare_key)
                            clear_chat_context()
                            time.sleep(retry_delay)
                            attempt += 1
                            retry_scheduled = True
                            break

                        processed_note = None
                        if rate_limited:
                            print(" [WARN] Secondary rate limit persisted after max retries. Keeping generated output.")
                            processed_note = "WARNING: secondary rate limit persisted after max retries"

                        log_processed(bare_key, elapsed, note=processed_note)
                        remove_epic_from_queue(QUEUE_FILE, epic_key)
                        completed = True
                        break

                    time.sleep(3)

                if completed:
                    break

                if retry_scheduled:
                    continue

                # Timeout for this attempt
                if (time.time() - start_time) >= MAX_WAIT_SECONDS:
                    print(f" ERROR: Timeout ({MAX_WAIT_SECONDS}s) reached for {bare_key}. Logging to epics_failed.txt...")
                    log_failure(bare_key, f"Timed out after {MAX_WAIT_SECONDS}s without producing XLSX")
                    remove_epic_from_queue(QUEUE_FILE, epic_key)
                    break

                # Reached here only when a rate-limit retry was scheduled.
                continue

            # Post-Epic Cleanup: Remove temporary files generated for this Epic
            cleanup_temp_files(bare_key)

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
                cleanup_temp_files(extract_jira_key(CURRENT_PROCESSING_EPIC))
            clear_chat_context()
            break
        except Exception as e:
            print(f"\n[ERROR] Unexpected loop crash: {e}")
            if CURRENT_PROCESSING_EPIC:
                # Epic was never removed from queue, so it will retry on next run
                cleanup_temp_files(extract_jira_key(CURRENT_PROCESSING_EPIC))
            clear_chat_context()
            break


if __name__ == "__main__":
    main()