import sqlite3
import json

conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    script_path TEXT NOT NULL,
    trigger_data TEXT NOT NULL,
    dependency_task_id INTEGER,
    dependency_condition TEXT,
    run_asap INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1
);
""")

def remove_task(task_id: int):
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()

def add_task(task_data: dict):
    new_task = {}
    new_task["name"] = task_data["name"]
    new_task["script_path"] = task_data["script"]

    trigger_type = task_data["trigger"]
    new_task["trigger"] = {"type": trigger_type}

    slot1 = task_data["slot1"]
    slot2 = task_data["slot2"]
    slot3 = task_data["slot3"]

    if trigger_type == "startup":
        pass  

    elif trigger_type == "interval":
        interval = slot1.query_one("#interval-selector").value.strip()
        start    = slot2.query_one("#start-time-selector").value.strip()

        dd, hh, mm = [int(s) for s in interval.split(":")]
        interval_secs = dd*24*3600 + hh*3600 + mm*60

        new_task["trigger"]["interval"] = interval_secs
        new_task["trigger"]["start"] = start

    elif trigger_type == "battery":
        condition = slot1.query_one("#battery-condition-selector").value
        pct       = slot2.query_one("#battery-percent-selector").value.strip()

        new_task["trigger"]["condition"] = condition
        new_task["trigger"]["percent"] = int(pct)

    elif trigger_type == "folder":
        folder_path = slot1.query_one("Input").value.strip()
        folder_event = slot2.query_one("#folder-condition-selector").value

        new_task["trigger"]["path"] = folder_path
        new_task["trigger"]["event"] = folder_event

        if folder_event == "folder-size-greater":
            threshold = slot3.query_one("Input").value.strip()
            new_task["trigger"]["threshold_gb"] = float(threshold)

    elif trigger_type == "keyboard":
        mods = slot1.query_one("#keyboard-mod-select").selected
        mods = [mod[1] for mod in mods]  # (label, value)

        key = slot2.query_one("#keyboard-key-select").label

        new_task["trigger"]["modifiers"] = mods
        new_task["trigger"]["key"] = key

    dep_row = task_data["dependency"]
    dep_task = dep_row.query_one("#dependency-task-select").value
    dep_cond = dep_row.query_one("#dependency-condition-select").value
    asap = 1 if task_data["asap"].value else 0

    new_task["dependency_task_id"] = dep_task
    new_task["dependency_condition"] = dep_cond
    new_task["run_asap"] = asap

    cursor.execute("""
        INSERT INTO tasks (name, script_path, trigger_data, dependency_task_id, dependency_condition, run_asap)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        new_task["name"],
        new_task["script_path"],
        json.dumps(new_task["trigger"]),
        new_task["dependency_task_id"],
        new_task["dependency_condition"],
        new_task["run_asap"]
    ))

    conn.commit()
