import asyncio
import os
from macroni.backend import db, dependency_handler

LOG_FILE_PATH = "log.txt"

async def run_script(task_id, path):

    open(LOG_FILE_PATH, "a").write(f"Running script for task {task_id}\n")
    
    # Check if the task on which this task depends has succeeded (or failed)
    if not dependency_handler.is_dependency_success(task_id):
        return False
    
    # Determine command based on file extension
    ext = os.path.splitext(path)[1].lower()

    if ext in [".bat", ".cmd"]:
        cmd = ["cmd.exe", "/c", path]

    elif ext == ".ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", path]

    elif ext == ".exe":
        cmd = [path]

    try:
        # Run the script asynchronously
        process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
        )
        out, err = await process.communicate()
        exit_code = process.returncode

        success = True if exit_code == 0 else False
        if success:
            try:
                db.cursor.execute( "UPDATE tasks SET last_run_success = ? WHERE id = ?",
                                    (1 if success else 0, task_id)
                                )
                db.conn.commit()
            except:
                pass
        return success
        
    except Exception as e:
        open(LOG_FILE_PATH, "a").write(f"Error running script for task {task_id}: {e}\n")
        return False


    