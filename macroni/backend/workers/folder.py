# backend/workers/folder.py
import asyncio
import json
import os
from datetime import datetime
from macroni.backend import db

RETRY_INTEVRAL_MIN = 5
RETRY_INTERVAL_CAP = 60


def get_folder_size_gb(path: str) -> float:
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                total += os.path.getsize(fp)
            except Exception:
                continue
    return total / (1024**3)


async def run_worker(task_row, run_script, stop_event: asyncio.Event):
    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    folder_path = trig.get("path")
    condition = trig.get("condition")
    threshold = float(trig.get("threshold", 0))

    if not folder_path:
        return

    # memory for detecting creations/deletions
    last_files = set()
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        last_files = set(os.listdir(folder_path))

    try:
        backoff = RETRY_INTEVRAL_MIN

        while not stop_event.is_set():

            if not os.path.exists(folder_path):
                # folder missing → skip
                await asyncio.sleep(RETRY_INTEVRAL_MIN)
                continue

            state_met = False

            # --- folder size condition ---
            if condition == "folder-size-greater":
                size_gb = get_folder_size_gb(folder_path)
                if size_gb > threshold:
                    state_met = True

            # --- file created ---
            elif condition == "folder-file-created":
                current_files = set(os.listdir(folder_path))
                created = current_files - last_files
                if created:
                    state_met = True
                last_files = current_files

            # --- file deleted ---
            elif condition == "folder-file-deleted":
                current_files = set(os.listdir(folder_path))
                deleted = last_files - current_files
                if deleted:
                    state_met = True
                last_files = current_files

            # --- run script if condition met ---
            if state_met:
                success = await run_script(task_id, task_row["script_path"])

                # retry if failure (same as interval worker)
                if not success:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                    continue

                # success → reset backoff
                backoff = RETRY_INTEVRAL_MIN

            # normal waiting (responsive to cancellation)
            slept = 0
            while slept < RETRY_INTEVRAL_MIN and not stop_event.is_set():
                await asyncio.sleep(1)
                slept += 1

    except asyncio.CancelledError:
        return
    except Exception as e:
        ts = datetime.now().isoformat(timespec="seconds")
        try:
            db.add_log(task_id, "", f"Worker exception: {e}", ts, 0)
        except Exception:
            pass
        return
