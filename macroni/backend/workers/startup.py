import json
from datetime import datetime
import asyncio
import macroni.backend.db as db
from macroni.backend.runscript import run_script  

async def main():
    conn = db.conn
    conn.row_factory = db.sqlite3.Row

    tasks = conn.execute("SELECT * FROM tasks").fetchall()

    startup_tasks = [t for t in tasks if json.loads(t["trigger_data"])["type"] == "startup"]

    print(f"Found {len(startup_tasks)} startup tasks")

    for task in startup_tasks:
        print(f"Running startup task: {task['name']}")
        await run_script(task["id"], task["script_path"])

    print("All startup tasks completed.")

if __name__ == "__main__":
    asyncio.run(main())
