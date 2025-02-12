import asyncio
import time
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    """Base class for handling file system changes with debouncing"""
    def __init__(self, server, extension):
        self.server = server
        self.last_scan = 0
        self.loop = asyncio.get_event_loop()
        self.extension = extension

    def on_modified(self, event):
        """Handle file modification events with 1-second debounce"""
        if event.src_path.endswith(self.extension):
            current_time = time.time()
            if current_time - self.last_scan > 1.0:
                self.last_scan = current_time
                self.trigger_scan()

class NodeChangeHandler(FileChangeHandler):
    """Handles Python file changes for node definitions"""
    def __init__(self, server):
        super().__init__(server, '.py')

    def trigger_scan(self):
        asyncio.run_coroutine_threadsafe(
            self.server.scan_nodes(), 
            self.loop
        )

class WorkflowChangeHandler(FileChangeHandler):
    """Handles JSON file changes for workflow definitions"""
    def __init__(self, server):
        super().__init__(server, '.json')

    def trigger_scan(self):
        asyncio.run_coroutine_threadsafe(
            self.server.scan_workflows(),
            self.loop
        )