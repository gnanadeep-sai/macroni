from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import LoadingIndicator, DataTable, Footer, Static, DirectoryTree
import directory, message, tasklist

class Macroni(App):
    """Class containing the Macroni app."""
    def compose(self) -> ComposeResult:
        # TODO
        pass

if __name__ == "__main__":
    app =  Macroni()
    app.run()
