# **Macroni – Automated Task Runner**

Macroni is a lightweight automation engine built with **Python + Textual**, designed to let users create, manage, and run scripts based on system events such as battery percentage, folder changes, hotkeys, intervals, and more.
It provides a full TUI for task creation and management, along with a backend worker system that runs triggers asynchronously.



### **Textual UI**

* Ability to select multiple tasks
* Create, edit, and delete tasks
* Directory picker with folder to folder navigation and file select detection
* Error popups
* Dynamic trigger-based fields

### **Scheduler**

Each task runs in its own worker (async loops)

* Tasks which run on boot
* Interval-based tasks
* Battery percent monitor
* Folder events (size threshold, file created, file deleted)
* Keyboard shortcut
* Tasks dependent on other tasks
* Ability to run asap after a failure


## **Installation**

### Clone the repository

```
git clone https://github.com/youruser/macroni.git
cd macroni
```

### Requirements:

```
pip install .
```

### Run the app

```
python -m macroni.main
```
---

## **Script Requirements**

Macroni supports running the following scripts:

* `.bat`
* `.ps1`
* `.exe`

## **Usage**
- On running `python -m macroni.main` you will have the app launch with a screen containing a table of all the tasks.

- Tasks can be selected in the table using `space` key (or mouse)

- Selected tasks can be deleted using `delete` key

- `^n` will take you to the new task screen where you can fill the form to add new tasks

- Dependent Tasks: These are tasks which have their own trigger types but to run the task, they need certain other task to be run successfully. 

