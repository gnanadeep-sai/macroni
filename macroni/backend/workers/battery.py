import asyncio
import json
from datetime import datetime
from macroni.backend.runscript import run_script
import psutil

# Minimum retry interval (seconds)
RETRY_INTERVAL_MIN = 5

# Max backoff interval (seconds)
RETRY_INTERVAL_CAP = 60


async def run_worker(task_row: dict, stop_event: asyncio.Event):
    """
    Background worker that monitors battery percentage and triggers a script
    based on the condition given by the user.

    Parameters
    ----------
    task_row : dict
        A DB row describing the task. Expected keys:
        - "id": Task ID
        - "trigger_data": JSON string with fields:
            * "condition": "greater" | "lesser" | "equal"
            * "percent": int (target battery percentage)
        - "script_path": Path of script to execute when condition is triggered.
    stop_event : asyncio.Event
        Event used to signal this worker to stop cleanly.
    """

    # Log worker start
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')}:  Starting battery worker for task {task_row['id']}\n")

    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    condition = trig.get("condition")
    target_pct = int(trig.get("percent", 0))

    # Tracks if the condition was already met i.e preventing double triggers
    last_state_met = False

    try:
        backoff = RETRY_INTERVAL_MIN

        while not stop_event.is_set():

            battery = psutil.sensors_battery()

            if battery is None:
                # Retry with increased interval each time
                backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                await asyncio.sleep(backoff)
                continue

            pct = int(battery.percent)
            state_met = False

            # Evaluate the condition
            if condition == "greater":
                state_met = pct > target_pct
            elif condition == "lesser":
                state_met = pct < target_pct
            elif condition == "equal":
                state_met = pct == target_pct

            # Checking if this is a new trigger
            if state_met and not last_state_met:
                await run_script(task_id, task_row["script_path"])

            last_state_met = state_met

            # Wait before the next iteration
            slept = 0
            while slept < RETRY_INTERVAL_MIN and not stop_event.is_set():
                await asyncio.sleep(1)
                slept += 1

    except Exception:
        pass
