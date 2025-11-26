from macroni.backend import db

cursor = db.cursor

def get_dependency(task_id: int):
    """
    Return the ID and condition of the task on which the given task depends.
    
    :param task_id: ID of the task whose dependency is to be fetched
    :type task_id: int
    """
    row = cursor.execute(
        "SELECT dependency_task_id, dependency_condition FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()
    return row

def is_dependency_success(task_id: int):
    """
    Return whether the last run of the specified task was successful.
    
    :param task_id: ID of the task whose success status is to be checked
    :type task_id: int
    """
    dependency = get_dependency(task_id)
    if not dependency:
        return True
    row = cursor.execute(
        "SELECT last_run_success FROM tasks WHERE id = ?", 
        (dependency["dependency_task_id"],)
    ).fetchone()
    success = row["last_run_success"]
    
    return success == 1
