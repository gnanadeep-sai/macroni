from textual.widgets import Static

class Message(Static):
    def on_mount(self):
        self.content = ""