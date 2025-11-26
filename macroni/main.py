import os
from pathlib import Path
import sys
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
import macroni.ui.tasklist as tasklist, macroni.ui.newtask as newtask
import winshell

class Macroni(App):
    """Class containing the Macroni app."""

    errors = []
    BINDINGS = [
        ("ctrl+n", "new_task", "Add new task")
    ]

    def on_mount(self):
        self.boot_setup()

    def action_new_task(self):
        self.push_screen(newtask.NewTask())
  
    def compose(self) -> ComposeResult:
        # TODO
        yield Header()
        yield tasklist.TaskList()
        yield Footer()
    
    def boot_setup(self):
        startup_dir = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        shortcut_path = startup_dir / "MacroniScheduler.lnk"
        if not shortcut_path.exists():
            python_exe = sys.executable  

            scheduler_script = (Path(__file__).resolve().parent / "backend" / "scheduler.py").resolve()

            winshell.CreateShortcut(
                Path=str(shortcut_path),
                Target=str(python_exe),
                Arguments=f'"{scheduler_script}"',
                StartIn=str(scheduler_script.parent),
                Description="Runs Macroni Scheduler at system startup"
            )

    
if __name__ == "__main__":
    app =  Macroni()
    app.run()
