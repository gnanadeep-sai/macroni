import asyncio
import json
from datetime import datetime, timedelta, time as dtime

from macroni.backend import db
from macroni.backend.runscript import run_script

RETRY_INTERVAL_MIN = 5
RETRY_INTERVAL_CAP = 60


async def wait_until(hhmm: str):
    """
    Sleep until a given "HH:MM" time.
    If the time has already passed today, wait until that time tomorrow.
    """
    try:
        hh, mm = [int(x) for x in hhmm.split(":")]
    except Exception:
        return

    while True:
        now = datetime.now()
        target = datetime.combine(now.date(), dtime(hour=hh, minute=mm))

        # If target time already passed, schedule for tomorrow
        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()

        # Sleep in small chunks so stop_event checks remain responsive (planned to use asyncio.Event().is_set() but)
        slept = 0
        while slept < wait_seconds:
            chunk = min(5, wait_seconds - slept)
            await asyncio.sleep(chunk)
            slept += chunk

        return


async def run_worker(task_row: dict, stop_event: asyncio.Event):
    """
    Interval-based worker.

    Runs a script every <interval> seconds.
    If 'start' is specified, waits until a specific HH:MM before starting.
    """
    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    interval = int(trig.get("interval", 0))
    start = trig.get("start")

    if interval <= 0:
        return

    # If a start time exists, block until that time hits
    if start:
        await wait_until(start)

    try:
        backoff = RETRY_INTERVAL_MIN

        while not stop_event.is_set():

            # Attempt to execute the script
            success = await run_script(task_id, task_row["script_path"])

            run_asap = bool(task_row.get("run_asap", 0))

            # Retry immediately with exponential backoff if needed
            if (not success) and run_asap:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                continue

            # Reset backoff after a successful run
            backoff = RETRY_INTERVAL_MIN

            # Sleep until next interval
            slept = 0
            while slept < interval and not stop_event.is_set():
                chunk = min(5, interval - slept)
                await asyncio.sleep(chunk)
                slept += chunk

    except asyncio.CancelledError:
        return

    except Exception as e:
        return
    