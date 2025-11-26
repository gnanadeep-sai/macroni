# backend/workers/folder.py

import asyncio
import json
import os
from macroni.backend.runscript import run_script

RETRY_INTERVAL_MIN = 5
RETRY_INTERVAL_CAP = 60


def get_inos(path: str) -> set:
    """
    Return a set of inode numbers for all files in the given directory.
    """
    inodes = set()
    for file_name in os.listdir(path):
        file_path = os.path.join(path, file_name)
        try:
            inodes.add(os.stat(file_path).st_ino)
        except Exception:
            continue
    return inodes


def get_folder_size_gb(path: str) -> float:
    """
    Return folder size in gigabytes.
    """
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
            except Exception:
                continue
    return total / (1024 ** 3)


async def run_worker(task_row: dict, stop_event: asyncio.Event):
    """
    Folder-monitor worker.
    
    Triggers when:
        - folder-size-greater: folder size goes over user given threshold
        - folder-file-created: new file appears
        - folder-file-deleted: file disappears
    """
    with open("log.txt", "a") as f:
        f.write(f"Starting folder worker for task {task_row['id']}\n")

    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    folder_path = trig.get("path")
    condition = trig.get("event")
    threshold = float(trig.get("threshold", 0))

    if not folder_path:
        return

    # Initial inode snapshot for file create/delete triggers (using inodes to avoid false triggers)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        last_files = get_inos(folder_path)
    else:
        last_files = set()

    # For size-based trigger we need to remember previous state to avoid repeated triggers
    last_state_met = False

    try:
        backoff = RETRY_INTERVAL_MIN

        while not stop_event.is_set():

            if not os.path.exists(folder_path):
                await asyncio.sleep(RETRY_INTERVAL_MIN)
                continue

            state_met = False


            if condition == "folder-size-greater":
                size_gb = get_folder_size_gb(folder_path)
                current_state = size_gb > threshold

                # Trigger only on first occurrence
                if current_state and not last_state_met:
                    state_met = True

                last_state_met = current_state


            elif condition == "folder-file-created":
                current_files = get_inos(folder_path)
                created = current_files - last_files

                if created:
                    state_met = True

                last_files = current_files

            elif condition == "folder-file-deleted":
                current_files = get_inos(folder_path)
                deleted = last_files - current_files

                if deleted:
                    state_met = True

                last_files = current_files

            # Trigger action if condition met
            if state_met:
                success = await run_script(task_id, task_row["script_path"])

                # Retry with increasing intervals on failure
                if not success:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                    continue

                # Reset backoff on success
                backoff = RETRY_INTERVAL_MIN

            # Wait before next iteration
            slept = 0
            while slept < RETRY_INTERVAL_MIN and not stop_event.is_set():
                await asyncio.sleep(1)
                slept += 1

    except Exception:
        return

    return
