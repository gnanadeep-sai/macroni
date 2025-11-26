import os

TASK_NAMES = [row["name"] for row in os.listdir("tasks_db")]  

# Validate form data and return a list of error messages. (Pretty evident from the error messages so not much commenting needed)
def validate_form(data):
    errors = []

    if not data["name"]:
        errors.append("Task name cannot be empty.")
    elif data["name"] in TASK_NAMES:
        errors.append("That taskname already exists. Pleace choose another one.")

    if not data["script"]:
        errors.append("Script path cannot be empty.")
    elif not os.path.isfile(data["script"]):
        errors.append("Invalid Script path given.")

    trigger = data["trigger"]

    if trigger == "interval":
        interval = data["slot1"].query_one("#interval-selector").value.strip()
        start    = data["slot2"].query_one("#start-time-selector").value.strip()

        if not interval:
            errors.append("Interval cannot be empty.")

        elif ":" not in interval or len(interval.split(":")) != 3:
            errors.append("Interval must be in DD:HH:MM format.")
        else:
            for s in interval.split(":"):
                if not s.isdigit():
                    errors.append("Invalid interval given.")
                    break
                elif int(s) < 0:
                    errors.append("Invalid Interval given.")
                    break
            
        if not start:
            errors.append("Start time cannot be empty.")
        elif ":" not in start or len(start.split(":")) != 2:
            errors.append("Start time must be in HH:MM format.")
        else:
            for s in start.split(":"):
                if not s.isdigit():
                    errors.append("Invalid interval given.")
                    break
                elif int(s) < 0:
                    errors.append("Invalid Interval given.")
                    break

    elif trigger == "battery":
        cond = data["slot1"].query_one("#battery-condition-selector").value
        pct  = data["slot2"].query_one("#battery-percent-selector").value.strip()

        if not pct.isdigit():
            errors.append("Battery percentage must be a number between 0-100.")
        else:
            pct_val = int(pct)
            if not (0 <= pct_val <= 100):
                errors.append("Battery percentage must be between 0-100.")

    elif trigger == "folder":
        path_box = data["slot1"].query_one("Input")
        folder_path = path_box.value.strip()

        cond = data["slot2"].query_one("#folder-condition-selector").value

        if not folder_path:
            errors.append("Folder path cannot be empty.")
        elif not os.path.isdir(folder_path):
            errors.append("Invalid folder path.")

        if cond == "folder-size-greater":
            thr = data["slot3"].query_one("Input").value.strip()
            if not thr:
                errors.append("Folder size threshold cannot be empty.")
            try:
                size_val = float(thr)
                if size_val < 0:
                    errors.append("Folder size threshold must be a positive number.")
            except:
                errors.append("Folder size threshold must be a valid number.")

    elif trigger == "keyboard":
        # modifier list (ctrl, alt etc): optional
        # key not opt
        btn = data["slot2"].query_one("#keyboard-key-select")
        if btn.label == "Click and press key":
            errors.append("Please press a key for the keyboard trigger.")
    
    dependency_task = data["dependency"].query_one("#dependency-task-select").is_blank()
    dependency_cond = data["dependency"].query_one("#dependency-condition-select").is_blank()

    if bool(dependency_task) ^ bool(dependency_cond):
        errors.append("Invalid dependendent task given. Make sure both the task and condition are selected.")

    return errors
