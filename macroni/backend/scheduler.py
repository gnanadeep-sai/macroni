import asyncio
import json
import os
from pathlib import Path
import sys
import winshell
import macroni.backend.db as db
from macroni.backend.workers import interval, battery

class Scheduler:
    def __init__(self):
        self.workers = []
        self.stops = {}

    async def start(self):
        tasks = self.load_tasks()
        self.startup_handler()

        for task in tasks:
            worker, stop_event = await self.handle_task(task)
            if worker:
                self.workers.append(worker)
                self.stops[f"{task['id']}"] = stop_event

    def load_tasks(self):
        """Return all DB rows"""
        conn = db.conn
        conn.row_factory = db.sqlite3.Row
        rows = conn.execute("SELECT * FROM tasks").fetchall()
        return rows

    async def handle_task(self, task):
        trigger = json.loads(task["trigger_data"])
        t = trigger["type"]

        if t == "startup":
            return self.startup_handler()

        if t == "interval":
            stop_event = asyncio.Event()
            return (asyncio.create_task(interval.run_worker(task, stop_event)), stop_event)

        elif t == "battery":
            stop_event = asyncio.Event()
            return (asyncio.create_task(battery.run_worker(task, stop_event)), stop_event)

        elif t == "folder":
            await self.folder_task(task, trigger)

        elif t == "keyboard":
            await self.keyboard_task(task, trigger)
    
    def startup_handler(self):
        startup_dir = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        shortcut_path = startup_dir / "MacroniStartup.lnk"

        if not shortcut_path.exists():
            python_exe = sys.executable

            startup_script = (Path(__file__).resolve().parent / "tasks" / "startup.py").resolve()

            winshell.CreateShortcut(
                Path=str(shortcut_path),
                Target=str(python_exe),
                Arguments=f'"{startup_script}"',
                StartIn=str(startup_script.parent),
                Description="Runs Macroni startup tasks"
            )

        return (None, None)

if __name__ == "__main__":
    async def main():
        scheduler = Scheduler()
        await scheduler.start()
        await asyncio.Event().wait()

    asyncio.run(main())
