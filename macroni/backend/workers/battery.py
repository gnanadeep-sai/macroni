# backend/workers/battery.py
import asyncio
import json
from datetime import datetime
from macroni.backend import db
from macroni.backend.runscript import run_script
import psutil

RETRY_INTERVAL_MIN = 5  # seconds
RETRY_INTERVAL_CAP = 60

async def run_worker(task_row, stop_event: asyncio.Event):
    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    condition = trig.get("condition")       # "greater", "lesser", "equal"
    target_pct = int(trig.get("percent", 0))

    last_state_met = False

    try:
        backoff = RETRY_INTERVAL_MIN
        while not stop_event.is_set():

            # read current battery status
            battery = psutil.sensors_battery()
            if battery is None:
                # unsupported system or no battery
                backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                continue

            pct = int(battery.percent)
            state_met = False

            if condition == "greater":
                state_met = pct > target_pct
            elif condition == "lesser":
                state_met = pct < target_pct
            elif condition == "equal":
                state_met = pct == target_pct

            # Trigger only when the state changes from NOT met → MET
            if state_met and not last_state_met:
                await run_script(task_id, task_row["script_path"])

            last_state_met = state_met

            # sleep in chunks so we stay responsive to cancellation
            slept = 0
            while slept < RETRY_INTERVAL_MIN and not stop_event.is_set():
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
