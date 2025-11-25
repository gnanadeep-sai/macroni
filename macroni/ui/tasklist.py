from textual.binding import Binding
from textual.widgets import DataTable
import macroni.backend.db as db
from macroni.ui.message import Message

class TaskList(DataTable):
    UNCHECKED_SYMBOL, CHECKED_SYMBOL = "☐", "☑"
    BINDINGS = [
        Binding("space", "select_cursor", "Select"),
        Binding("delete", "delete_task", "Delete")
    ]

    def on_mount(self):
        self.add_columns(("", "select"), ("Task Name","task-name"), ("Type", "type"), ("Next Run", "next-run"), ("Last Run", "last-run"))
        # adding rows from database
        self.add_row("☐", "Cleanup", "Startup", "in 2 hrs", "Success", key="1") #temp
        self.add_row("☐", "Backup", "Startup", "in 2 hrs", "Success", key="2") #temp

    def add_task(self, key, task):
        try:
            self.add_row(self.UNCHECKED_SYMBOL, *task, key = key)
            # updating the databasee
        
        except Exception as e:
            self.log(f"Failed to add task: {e}")
    
    def action_delete_task(self):
        selected_keys = self.get_selected_row_keys()
        if len(selected_keys) == 0:
            return
        tasks = 0
        for key in selected_keys:
            try:
                db.remove_task(key)
                self.remove_row(key)
                tasks += 1

            except Exception as e:
                self.log(f"Failed to delete task: {e}")
                
        self.reset_selection()
        self.log(f"Successfully deleted {tasks} task(s)")

    def edit_task(self, key, updated_task):
        if len(updated_task) != len(self.columns):
            self.log(f"Failed to edit row: All parameters are not provided")
        try:
            self.remove_row(key)
            self.add_task(key, *updated_task)
        except Exception as e:
            self.log(f"Failed to edit row: {e}")

    def get_selected_row_keys(self):
        out = []
        for key, row in self.rows.items():
            if self.get_cell(key, "select") == self.CHECKED_SYMBOL:
                out.append(key)
        return out
        
    def on_data_table_row_selected(self, event):
        row_key = event.row_key.value
        current = self.get_cell(row_key, "select")
        new = self.CHECKED_SYMBOL if current == self.UNCHECKED_SYMBOL else self.UNCHECKED_SYMBOL
        self.update_cell(row_key, "select", new)
    
    def reset_selection(self):
        for key, row in self.rows.items():
            self.update_cell(key, "select", self.UNCHECKED_SYMBOL)

    def log(self, message:str):
        self.app.log(message)
        logger = self.app.query_one(Message)
        logger.update(f"{message}")

    def __init__(self):
        super().__init__()
        self.cursor_type = "row"