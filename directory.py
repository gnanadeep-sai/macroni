from time import monotonic
from textual.binding import Binding
from textual.widgets import DirectoryTree

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