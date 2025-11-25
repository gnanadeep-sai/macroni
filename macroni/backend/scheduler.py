import asyncio
import json
import macroni.backend.db as db
from datetime import datetime
from backend.runscript import run_script

class Scheduler:
    def __init__(self):
        self.workers = []

    async def start(self):
        tasks = self.load_tasks()

        for task in tasks:
            worker = asyncio.create_task(self.handle_task(task))
            self.workers.append(worker)

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
            await self.startup_task(task, trigger)

        elif t == "interval":
            await self.interval_task(task, trigger)

        elif t == "battery":
            await self.battery_task(task, trigger)

        elif t == "folder":
            await self.folder_task(task, trigger)

        elif t == "keyboard":
            await self.keyboard_task(task, trigger)

    async def startup_task(self, task, trig):
        await run_script(task["script_path"])
