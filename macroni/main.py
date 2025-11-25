from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import LoadingIndicator, DataTable, Footer, Static, DirectoryTree
from textual.widgets._button import Button
from textual.widgets._header import Header
from textual.widgets._input import Input
import macroni.ui.directory as directory, macroni.ui.message as message, macroni.ui.tasklist as tasklist, macroni.ui.newtask as newtask, macroni.ui.errorscreen as errorscreen

class Macroni(App):
    """Class containing the Macroni app."""

    errors = []
    BINDINGS = [
        ("ctrl+n", "new_task", "Add new task")
    ]

    def on_mount(self):
        pass

    def action_new_task(self):
        self.push_screen(newtask.NewTask())
  
    def compose(self) -> ComposeResult:
        # TODO
        yield Header()
        yield tasklist.TaskList()
        yield Footer()
    


if __name__ == "__main__":
    app =  Macroni()
    app.run()
