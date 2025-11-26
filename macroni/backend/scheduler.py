import asyncio
import json
import os
from pathlib import Path
import sys
import winshell
import macroni.backend.db as db
from macroni.backend.workers import folder, interval, battery, keyboard

class Scheduler:
    """Class that manages all background workers based on DB tasks."""
    def __init__(self):
        self.workers = {}
        self.stops = {}
        self.tasks_snapshot = {} # cache of task data to detect changes

    async def start(self):
        tasks = self.load_tasks() 
        self.startup_handler() # Ensure startup script is set

        for task in tasks:
            await self.start_task(task)

        # Start DB watcher to detect changes
        asyncio.create_task(self.watch_db_loop())

    def load_tasks(self):
        """Return all DB rows"""
        conn = db.conn
        conn.row_factory = db.sqlite3.Row
        rows = conn.execute("SELECT * FROM tasks").fetchall()
        return rows

    async def start_task(self, task):
        """Start a new worker based on task data."""
        trigger = json.loads(task["trigger_data"])
        t = trigger["type"]

        task_id = str(task["id"])

        # Skip startup tasks as they are handled separately
        if t == "startup":
            return
        
        if t == "interval":
            stop_event = asyncio.Event()
            worker = asyncio.create_task(interval.run_worker(task, stop_event))

        elif t == "battery":
            stop_event = asyncio.Event()
            worker = asyncio.create_task(battery.run_worker(task, stop_event))

        elif t == "keyboard":
            stop_event = asyncio.Event()
            worker = asyncio.create_task(keyboard.run_worker(task, stop_event))
        
        elif t == "folder":
            stop_event = asyncio.Event()
            worker = asyncio.create_task(folder.run_worker(task, stop_event))

        self.workers[task_id] = worker
        self.stops[task_id] = stop_event
        self.tasks_snapshot[task_id] = dict(task) # store snapshot

    async def stop_task(self, task_id):
        """Cancel and remove an existing worker."""
        if task_id in self.stops:
            self.stops[task_id].set()

        if task_id in self.workers:
            self.workers[task_id].cancel()
            try:
                await self.workers[task_id]
            except:
                pass

        self.workers.pop(task_id, None)
        self.stops.pop(task_id, None)
        self.tasks_snapshot.pop(task_id, None)

    async def watch_db_loop(self):
        """Continuously watch DB for changes."""
        while True:
            await asyncio.sleep(1)  # check every second
            await self.check_for_updates()

    async def check_for_updates(self):
        """Compare DB state with snapshot and update workers."""
        current = {}
        for row in self.load_tasks():
            task_id = str(row["id"])
            task_data = dict(row)
            current[task_id] = task_data

        old = self.tasks_snapshot # existing snapshot

        # Update existing tasks if changed, start new tasks, stop removed tasks
        
        for tid, task in current.items():
            if tid not in old:
                await self.start_task(task)

        
        for tid in list(old.keys()):
            if tid not in current:
                await self.stop_task(tid)


    def startup_handler(self):
        """Ensure Macroni startup script is set to run on system startup."""

        startup_dir = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        shortcut_path = startup_dir / "MacroniStartup.lnk"

        if not shortcut_path.exists():
            python_exe = sys.executable
            
            # Create shortcut to run startup tasks
            winshell.CreateShortcut(
                Path=str(shortcut_path),
                Target=str(python_exe),
                Arguments="-m macroni.backend.startup",
                StartIn=str(Path(__file__).resolve().parent.parent.parent),
                Description="Runs Macroni startup tasks"
            )

if __name__ == "__main__":
    async def main():
        scheduler = Scheduler()
        await scheduler.start()
        await asyncio.Event().wait()

    asyncio.run(main())
