import json
from textual.binding import Binding
from textual.widgets import DataTable
import macroni.backend.db as db
from textual.widgets import Footer, Header

class TaskList(DataTable):
    """A data table to display and manage tasks."""

    # Symbols for unchecked and checked states in the selection column
    UNCHECKED_SYMBOL, CHECKED_SYMBOL = "☐", "☑"
    BINDINGS = [
        Binding("space", "select_cursor", "Select"),
        Binding("delete", "delete_task", "Delete")
    ]

    def on_show(self):
        """Populate the task list when the screen is shown."""

        self.add_columns(("", "select"), ("Task Name","task-name"), ("Type", "type"), ("Last Run", "last-run"), ("Script Path", "script-path"))
        db_cursor = db.cursor.execute("SELECT id, name, trigger_data, last_run_success, script_path FROM tasks")
        tasks = db_cursor.fetchall()
        for task in tasks:
            task_id, name, trigger_data, last_run_success, script_path = task
            trig = json.loads(trigger_data)
            trig_type = trig["type"].capitalize()
            last_run = "Success" if last_run_success else "Failure"
            self.add_row(self.UNCHECKED_SYMBOL, name, trig_type, last_run, script_path, key=str(task_id))
    
    def action_delete_task(self):
        """Delete selected tasks from the database and the table."""
        
        selected_keys = self.get_selected_row_keys()
        if len(selected_keys) == 0:
            return
        tasks = 0
        for key in selected_keys:
            try:
                db.remove_task(int(key))
                self.remove_row(key)
                tasks += 1

            except Exception as e:
                self.log(f"Failed to delete task: {e}")
                
        self.reset_selection()
        self.log(f"Successfully deleted {tasks} task(s)")

    def get_selected_row_keys(self):
        """Return a list of keys for the selected rows."""
        out = []
        for key, row in self.rows.items():
            if self.get_cell(key, "select") == self.CHECKED_SYMBOL:
                out.append(key.value)
        return out
        
    def on_data_table_row_selected(self, event):
        """Toggle selection state of the selected row."""
        row_key = event.row_key.value
        current = self.get_cell(row_key, "select")
        new = self.CHECKED_SYMBOL if current == self.UNCHECKED_SYMBOL else self.UNCHECKED_SYMBOL
        self.update_cell(row_key, "select", new)
    
    def reset_selection(self):
        """Reset all rows to unchecked state."""
        for key, row in self.rows.items():
            self.update_cell(key, "select", self.UNCHECKED_SYMBOL)

    def log(self, message:str):
        self.app.log(message)
        open("log.txt", "a").write(message + "\n")

    def __init__(self):
        super().__init__()
        self.cursor_type = "row"

class TaskListScreen(TaskList):
    def compose(self):
        yield Header()
        yield TaskList()
        yield Footer()