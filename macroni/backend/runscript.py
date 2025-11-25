import asyncio
from datetime import datetime
import os

LOG_FILE_PATH = "log.txt"

async def run_script(task_id, path):
    ext = os.path.splitext(path)[1].lower()

    if ext in [".bat", ".cmd"]:
        cmd = ["cmd.exe", "/c", path]

    elif ext == ".ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", path]

    elif ext == ".py":
        cmd = ["python", path]

    elif ext == ".sh":
        cmd = ["bash", path]


    elif ext == ".exe":
        cmd = [path]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    out, err = await process.communicate()
    stdout = out.decode(errors="ignore")
    stderr = err.decode(errors="ignore")
    timestamp = datetime.now().isoformat(timespec="seconds")

    logs = open(LOG_FILE_PATH, "a")
    logs.write(f"{timestamp}: Task {task_id} finished\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}\n\n")