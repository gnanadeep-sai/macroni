from time import monotonic
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DirectoryTree, Header, Footer

import macroni.ui.newtask as newtask

class Directory(DirectoryTree):
    last_click_time = 0
    last_click_path = None
    DOUBLE_CLICK_THRESHOLD = 0.5

    BINDINGS = [
        Binding("backspace", "go_up", "Go to Parent")
    ]

    ALLOWED_EXTS = {".sh", ".exe", ".py", ".bat1", ".ps1"}   

    def filter_paths(self, paths):
        """Return only allowed extensions."""
        for p in paths:
            if p.is_dir():
                yield p
            else:
                if p.suffix.lower() in self.ALLOWED_EXTS:
                    yield p

    def is_double_click(self, path):
        current_time = monotonic()
        out = False
        if (self.last_click_path == path and (current_time - self.last_click_time) <= self.DOUBLE_CLICK_THRESHOLD):
            out = True
        self.last_click_time = current_time
        self.last_click_path = path
        return out

    def on_directory_tree_directory_selected(self, event):
        f = open("test.txt", "a")
        f.write("sskjdhkjhd")
        if self.is_double_click(event.path):
            if event.path == self.path:
                self.path = self.path.absolute().parent
            else:
                self.path = event.path

    def on_directory_tree_file_selected(self, event):
        if self.is_double_click(event.path):
            self.screen.dismiss(event.path)

    def action_go_up(self):
        self.path = self.path.absolute().parent

    def on_mount(self):
        self.path = self.path.absolute()
    
    def __init__(self):
        super().__init__(path='.')

class DirectoryScreen(Screen):
    def compose(self):
        yield Header()
        yield Directory()
        yield Footer()