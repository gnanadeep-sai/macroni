from time import monotonic
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import LoadingIndicator, DataTable, Footer, Static, DirectoryTree

ACTIVE_TASKS = [{"name":"test", "type": "startup"}, {"name":"test", "type": "startup"}, {"name":"test", "type": "startup", }]
UNCHECKED_SYMBOL, CHECKED_SYMBOL = "☐", "☑"

class TaskList(DataTable):
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
            self.add_row(UNCHECKED_SYMBOL, *task, key = key)
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
                self.remove_row(key)
                tasks += 1
                # updating the database
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
            if self.get_cell(key, "select") == CHECKED_SYMBOL:
                out.append(key)
        return out
        
    def on_data_table_row_selected(self, event):
        row_key = event.row_key.value
        current = self.get_cell(row_key, "select")
        new = CHECKED_SYMBOL if current == UNCHECKED_SYMBOL else UNCHECKED_SYMBOL
        self.update_cell(row_key, "select", new)
    
    def reset_selection(self):
        for key, row in self.rows.items():
            self.update_cell(key, "select", UNCHECKED_SYMBOL)

    def log(self, message:str):
        self.app.log(message)
        logger = self.app.query_one(Message)
        logger.update(f"{message}")

    def __init__(self):
        super().__init__()
        self.cursor_type = "row"

class Message(Static):
    def on_mount(self):
        self.content = ""

class Directory(DirectoryTree):
    last_click_time = 0
    last_click_path = None
    DOUBLE_CLICK_THRESHOLD = 0.5

    BINDINGS = [
        Binding("backspace", "go_up", "Go to Parent")
    ]

    def on_directory_tree_directory_selected(self, event):
        now = monotonic()
        if (self.last_click_path == event.path and (now - self.last_click_time) <= self.DOUBLE_CLICK_THRESHOLD):
            if event.path == self.root:
                self.path = self.path.absolute().parent
            else:
                self.path = event.path

        self.last_click_time = now
        self.last_click_path = event.path
    
    def action_go_up(self):
        self.path = self.path.absolute().parent
    
    def on_mount(self):
        self.path = self.path.absolute()


class Macroni(App):
    """Class containing the Macroni app."""
    def compose(self) -> ComposeResult:
        # TODO
        pass



if __name__ == "__main__":
    app =  Macroni()
    app.run()
