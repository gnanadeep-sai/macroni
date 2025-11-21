from textual.app import App, ComposeResult
from textual.widgets import LoadingIndicator, DataTable

ACTIVE_TASKS = [{"name":"test", "type": "startup"}, {"name":"test", "type": "startup"}, {"name":"test", "type": "startup", }]
UNCHECKED_SYMBOL, CHECKED_SYMBOL = "☐", "☑"

class TaskList(DataTable):

    def on_mount(self):
        self.add_columns(("", "select"), ("Task Name","task-name"), ("Type", "type"), ("Next Run", "next-run"), ("Last Run", "last-run"))
        # adding rows from database
        self.add_row("☐", "Cleanup", "Startup", "in 2 hrs", "Success", key="1") #temp
        self.add_row("☐", "Backup", "Startup", "in 2 hrs", "Success", key="2") #temp

    def get_selected_row_ids(self):
        out = []
        for key, row in self.rows.items():
            if row[0] == CHECKED_SYMBOL:
                out.append(key)
        return out
        
    def on_data_table_row_selected(self, event):
        row_key = event.row_key.value
        current = self.get_cell(row_key, "select")
        new = CHECKED_SYMBOL if current == UNCHECKED_SYMBOL else UNCHECKED_SYMBOL
        self.update_cell(row_key, "select", new)

    def __init__(self):
        super().__init__()
        self.cursor_type = "row"


class Macroni(App):
    """Class containing the Macroni app."""
    def compose(self) -> ComposeResult:
        yield TaskList()


if __name__ == "__main__":
    app =  Macroni()
    app.run()
