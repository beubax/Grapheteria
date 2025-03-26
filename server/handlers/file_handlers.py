import asyncio
import time
from watchdog.events import FileSystemEventHandler
from server.utils.scanner import SystemScanner

class FileChangeHandler(FileSystemEventHandler):
    """Base class for handling file system changes with debouncing"""
    def __init__(self, manager, extension):
        self.manager = manager
        self.last_scan = 0
        self.loop = asyncio.get_event_loop()
        self.extension = extension

    def on_modified(self, event):
        """Handle file modification events with 1-second debounce"""
        if event.src_path.endswith(self.extension):
            current_time = time.time()
            if current_time - self.last_scan > 1.0:
                self.last_scan = current_time
                self.last_modified_path = event.src_path
                self.trigger_scan()

class NodeChangeHandler(FileChangeHandler):
    """Handles Python file changes for node definitions"""
    def __init__(self, manager):
        super().__init__(manager, '.py')

    def trigger_scan(self):
        asyncio.run_coroutine_threadsafe(
            self.manager.scan_nodes(), 
            self.loop
        )

class WorkflowChangeHandler(FileChangeHandler):
    """Handles JSON file changes for workflow definitions"""
    def __init__(self, manager):
        super().__init__(manager, '.json')

    def trigger_scan(self):
        asyncio.run_coroutine_threadsafe(
            self.manager.scan_workflow_file(self.last_modified_path),
            self.loop
        )