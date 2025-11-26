# backend/workers/keyboard.py
import asyncio
import json
from datetime import datetime
import threading
from macroni.backend import db
import keyboard
from macroni.backend.runscript import run_script  

RETRY_INTEVRAL_MIN = 5
RETRY_INTERVAL_CAP = 60


keyboard_trigger_flags = {}


def _keyboard_listener(task_id, modifiers, main_key):

    combo = "+".join(modifiers + [main_key])

    def on_hotkey():
        keyboard_trigger_flags[task_id] = True

    keyboard.add_hotkey(combo, on_hotkey)

    keyboard.wait()  


async def run_worker(task_row, stop_event: asyncio.Event):
    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    modifiers = trig.get("modifiers", [])   
    main_key = trig.get("key")              

    if not main_key:
        return

    keyboard_trigger_flags[task_id] = False


    listener_thread = threading.Thread(
        target=_keyboard_listener,
        args=(task_id, modifiers, main_key),
        daemon=True
    )
    listener_thread.start()

    try:
        backoff = RETRY_INTEVRAL_MIN

        while not stop_event.is_set():

            if keyboard_trigger_flags.get(task_id, False):

                success = await run_script(task_id, task_row["script_path"])

                if not success:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                    continue

                backoff = RETRY_INTEVRAL_MIN
                keyboard_trigger_flags[task_id] = False

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
