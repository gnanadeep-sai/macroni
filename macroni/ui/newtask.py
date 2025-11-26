
from macroni.ui import tasklist
from textual import events
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Static, Input, Button, Header, Select, Checkbox, SelectionList
from textual.widgets._input import Selection
import macroni.backend.db as db
import macroni.ui.directory as directory
import macroni.ui.validation as validation, macroni.ui.errorscreen as errorscreen

TRIGGER_TYPES = [
    ("Startup", "startup"),
    ("Interval", "interval"),
    ("Battery", "battery"),
    ("Folder/Disk Events", "folder"),
    ("Keyboard Shortcut", "keyboard")
]

TASK_NAMES = [(t['name'], t['id']) for t in db.get_all_tasks()]

class NewTask(Screen):
    """A screen to add a new task."""

    TITLE = "Add New Task"
    OPTIONS = TRIGGER_TYPES
    CSS_PATH = "newtask.tcss"
    errors = []
    def compose(self):
        yield Header()
        yield Static("")

        yield Horizontal(
        Input(placeholder="Task Name", id="task-name-input"),
        Button("X", id="clear")
        , id="task-name-input-holder")
        
        yield Horizontal(
            Input(placeholder="Path to script", id="path-input"),
            Button("Select Script", id="select"),
            id = "path-holder")
        
        yield Horizontal(
            Select(options=self.OPTIONS, prompt="Trigger type", id="type-select-dropdown", allow_blank=False),
            Static(classes="hidden slot"),
            Static(classes="hidden slot"),
            Static(classes="hidden slot"),
            id="trigger-row"
        )

        # Dependency row to run only if another task succeeded/failed
        yield Horizontal(
            Input(value="Run only if:", disabled=True),
            Select(options=TASK_NAMES, prompt="Select task", id="dependency-task-select"),
            Select(options=[("last run succeeded", "succeed"), ("last run failed", "failed")], prompt="Select condition", id="dependency-condition-select"),
            id="dependency-row"
        )
        yield Checkbox("Run ASAP in case of failure?", id="asap", button_first=False)
        yield Horizontal(
            Button(label="Submit", id="submit"),
            Button(label="Reset", id="reset-fields"),
            id="submit-row")
    
    # Reset dynamic slots (slot1, slot2, slot3)
    def reset_slots(self):
        slots = self.query(".slot")
        i = 1
        for s in slots:
            s.set_classes(f"slot").display = False
            s.remove_children()
            i += 1
        return slots
    
    def on_select_changed(self, event: Select.Changed):
        
        if event.select.id == "type-select-dropdown":
            slot1, slot2, slot3 = self.reset_slots()
        
        if event.select.id == "folder-condition-selector":
            slot3 = self.query(".slot")[2]
            slot3.remove_children()
            slot3.display = False
            
        if event.value == "interval":

            slot1.add_class("interval-selector-slot").display = True
            slot2.add_class("start-selector-slot").display = True

            slot1.mount(Input(placeholder="Enter Interval (DD:HH:MM)", id="interval-selector"))
            slot2.mount(Input(placeholder="Enter Start Time (HH:MM)", id="start-time-selector"))
        
        if event.value == "battery":

            slot1.add_class("battery-condition-selector-slot").display = True
            slot2.add_class("battery-pct-selector-slot").display = True

            slot1.mount(Select
                        (options=[("Rises above", "greater"),
                                    ("Falls Below", "lesser"),
                                    ("Equals", "equal")],
                         id="battery-condition-selector", allow_blank=False))
            slot2.mount(Input(placeholder="Enter Battery Percentage", id="battery-percent-selector"))
        
        if event.value == "folder":
            slot1.add_class("folder-selector-slot").display = True
            slot2.add_class("folder-condition-selector-slot").display = True
            slot1.mount(Input(placeholder="Please enter folder path"))
            slot2.mount(Select
                        (options=[("Size occupied goes above", "folder-size-greater"),
                                    ("File created", "folder-file-created"),
                                    ("File deleted", "folder-file-deleted")],
                         id="folder-condition-selector", allow_blank=False))

        if event.value == "keyboard":
            slot1.add_class("keybind-mod-slot").display = True
            slot2.add_class("keybind-key-slot").display = True
            slot1.mount(
                SelectionList[str](
                    Selection("ctrl", "ctrl"),
                    Selection("shift", "shift"),
                    Selection("alt", "alt"),
                    Selection("windows", "win")
                , id="keyboard-mod-select")
            )

            slot2.mount(Button(label="Click and press key", id="keyboard-key-select"))

        if event.value == "folder-size-greater":
            slot3.add_class("folder-threshold-selector-slot").display = True
            slot3.mount(Input(placeholder="Enter size in GB"))

    def on_key(self, event:events.Key):
        """Handle key presses for keyboard shortcut selection."""
        try:
            input_box = self.query_one("#keyboard-key-select")
        except:
            return
        if not input_box.has_focus:
            return
        
        cleaned_letter = event.name
        stripper = ["ctrl_", "shift_", "alt_", "win_", "upper_"]
        for strip in stripper:
            cleaned_letter = cleaned_letter.replace(strip, "") # Remove modifier prefixes
        input_box.label = cleaned_letter
        
    def on_button_pressed(self, event):

        # Clear task name input
        if event.button.id == "clear":
            self.query_one("#task-name-input", Input).value = ""
            self.set_focus(self.query_one("#task-name-input", Input))

        # Open directory screen to select script    
        if event.button.id == "select":
            self.app.push_screen(directory.DirectoryScreen(), self.on_file_selected)
        
        if event.button.id == "submit":
            data = self.get_form_data()
            self.errors = validation.validate_form(data).copy()
            if len(self.errors) == 0:
                db.add_task(data)
                self.app.query_one(tasklist.TaskList).refresh(recompose=True)
                self.app.pop_screen()
            else:
                self.app.errors = self.errors.copy()
                self.app.push_screen(errorscreen.ErrorScreen())

        if event.button.id == "reset-fields":
            self.reset_form()

    def get_form_data(self):
        """Retrieve data from the form inputs."""
        data = {}

        # Task name
        data["name"] = self.query_one("#task-name-input", Input).value.strip()

        # Script path
        data["script"] = self.query_one("#path-input", Input).value.strip()

        # Trigger type
        trigger = self.query_one("#type-select-dropdown", Select).value
        data["trigger"] = trigger

        # Dynamic slot inputs
        slots = self.query(".slot")
        data["slot1"] = slots[0]
        data["slot2"] = slots[1]
        data["slot3"] = slots[2]
        
        # Dependency
        dependency = self.query_one("#dependency-row")
        data["dependency"] = dependency

        data["asap"] = self.query_one("#asap")

        return data    

    def reset_form(self):
        """Reset all form fields to default state."""
        
        self.query_one("#task-name-input", Input).value = ""
        self.query_one("#path-input", Input).value = ""

        type_dropdown = self.query_one("#type-select-dropdown")
        type_dropdown.value = "startup"

        slots = self.query(".slot")
        for s in slots:
            s.remove_children()
            s.display = False
            s.set_classes("slot")

        self.query_one("#dependency-task-select").clear()
        self.query_one("#dependency-condition-select").clear()

        self.query_one("#asap").value = False

    def on_file_selected(self, path):
        self.query_one("#path-input").value = f"{path}"