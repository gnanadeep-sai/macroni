from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
import macroni.ui.tasklist as tasklist, macroni.ui.newtask as newtask

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
