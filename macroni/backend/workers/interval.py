import asyncio
import json
from datetime import datetime, timedelta, time as dtime

from macroni.backend import db

RETRY_INTEVRAL_MIN = 5
RETRY_INTERVAL_CAP = 60

async def wait_until(hhmm: str):
    try:
        hh, mm = [int(x) for x in hhmm.split(":")]
    except Exception:
        return
    while True:
        now = datetime.now()
        target = datetime.combine(now.date(), dtime(hour=hh, minute=mm))
        if now > target:
            target += timedelta(days=1)
        wait = (target - now).total_seconds()
        slept = 0
        while slept < wait:
            await asyncio.sleep(min(5, wait - slept))
            slept += min(5, wait - slept)
        return

async def run_worker(task_row, run_script, stop_event: asyncio.Event):
    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])
    interval = int(trig.get("interval", 0))
    start = trig.get("start")

    if interval <= 0:
        return

    if start:
        await wait_until(start)

    try:
        backoff = RETRY_INTEVRAL_MIN
        while not stop_event.is_set():

            success = await run_script(task_id, task_row["script_path"])

            run_asap = bool(task_row.get("run_asap", 0))
            if (not success) and run_asap:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                continue

            slept = 0
            while slept < interval and not stop_event.is_set():
                await asyncio.sleep(min(5, interval - slept))
                slept += min(5, interval - slept)

    except asyncio.CancelledError:
        return
    except Exception as e:
        ts = datetime.now().isoformat(timespec="seconds")
        try:
            db.add_log(task_id, "", f"Worker exception: {e}", ts, 0)
        except Exception:
            pass
        return
