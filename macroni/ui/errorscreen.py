from textual.widgets import Label, Button
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.containers import Grid

class ErrorScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("", id="errors"),
            Button("Ok", variant="error", id="quit"),
            id="dialog",
        )
    
    def on_mount(self):
        errors = "\n".join(f"- {e}" for e in self.app.errors)
        self.query_one("#errors", Label).update(content=errors)
    
    def on_show(self):
        errors = "\n".join(f"- {e}" for e in self.app.errors)
        self.query_one("#errors", Label).update(content=errors)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()
    
    