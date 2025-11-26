# backend/workers/keyboard.py

import asyncio
import json
import threading
from datetime import datetime

import keyboard
from macroni.backend import db
from macroni.backend.runscript import run_script

# Minimum retry interval (seconds)
RETRY_INTERVAL_MIN = 5

# Capping the ever increasing retry interval (seconds)
RETRY_INTERVAL_CAP = 60

# Each task_id stores a boolean flag to indicate hotkey press
keyboard_trigger_flags = {}


def _keyboard_listener(task_id: int, modifiers: list, main_key: str):
    """
    Keyboard listener.

    When the specified hotkey combination is pressed, it sets a flag
    that the worker loop checks.
    Parameters
    ----------
    task_id : int
        ID of the task.
    modifiers : list
        List of modifier keys (e.g., ["ctrl", "alt"]).
    main_key : str
        The main key for the hotkey combination.
    """

    combo = "+".join(modifiers + [main_key])

    def on_hotkey():
        with open("log.txt", "a") as f:
            f.write(
                f"{datetime.now().isoformat(timespec='seconds')}:  "
                f"Hotkey {combo} pressed for task {task_id}\n"
            )
        keyboard_trigger_flags[task_id] = True

    keyboard.add_hotkey(combo, on_hotkey)
    keyboard.wait()  # runs forever


async def run_worker(task_row: dict, stop_event: asyncio.Event):
    """
    Background worker that waits for a hotkey press and triggers a script
    when the user-defined keyboard combination is detected.

    Parameters
    ----------
    task_row : dict
        Expected fields:
        - "id": Task ID
        - "trigger_data": JSON string with:
            * "modifiers": list of modifier keys
            * "key": main key
        - "script_path": Path of script to run when the hotkey is pressed.
    stop_event : asyncio.Event
        Signals the worker to stop cleanly.
    """

    with open("log.txt", "a") as f:
        f.write(
            f"{datetime.now().isoformat(timespec='seconds')}:  "
            f"Starting keyboard worker for task {task_row['id']}\n"
        )

    task_id = task_row["id"]
    trig = json.loads(task_row["trigger_data"])

    modifiers = trig.get("modifiers", [])
    main_key = trig.get("key")

    # Hotkey must include a main key
    if not main_key:
        return

    # Reset detection flag for this worker
    keyboard_trigger_flags[task_id] = False

    # Keyboard listener thread creation
    listener_thread = threading.Thread(
        target=_keyboard_listener,
        args=(task_id, modifiers, main_key),
        daemon=True
    )
    listener_thread.start()

    try:
        backoff = RETRY_INTERVAL_MIN

        while not stop_event.is_set():

            # Hotkey was pressed
            if keyboard_trigger_flags.get(task_id, False):

                success = await run_script(task_id, task_row["script_path"])

                # Retry with increasing intervals
                if not success:
                    await asyncio.sleep(1)
                    backoff = min(backoff * 2, RETRY_INTERVAL_CAP)
                    continue

                # Update last_run_success 
                try:
                    db.cursor.execute(
                        "UPDATE tasks SET last_run_success = ? WHERE id = ?",
                        (1 if success else 0, task_id)
                    )
                    db.conn.commit()
                except Exception:
                    pass

                # Reset flags and backoff after successful run
                backoff = RETRY_INTERVAL_MIN
                keyboard_trigger_flags[task_id] = False

            # Wait before next iteration
            slept = 0
            while slept < RETRY_INTERVAL_MIN and not stop_event.is_set():
                await asyncio.sleep(1)
                slept += 1

    except:
        return
