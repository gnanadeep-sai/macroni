import json
import asyncio
import macroni.backend.db as db
from macroni.backend.runscript import run_script  

async def main():

    # Connect to database
    conn = db.conn
    conn.row_factory = db.sqlite3.Row

    tasks = conn.execute("SELECT * FROM tasks").fetchall()

    startup_tasks = []
    for t in tasks:
        if json.loads(t["trigger_data"])["type"] == "startup":
            startup_tasks.append(t)

    # Run each startup task script
    for task in startup_tasks:
        await run_script(task["id"], task["script_path"])

if __name__ == "__main__":
    asyncio.run(main())
