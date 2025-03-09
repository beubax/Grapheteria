import asyncio
import websockets
from watchdog.observers import Observer
from server.workflow_server import WorkflowServer
from server.handlers.file_handlers import NodeChangeHandler, WorkflowChangeHandler, LogWatcher

async def main():
    """Main server entry point"""
    server = WorkflowServer()
    
    # Configure file system watchers
    observer = Observer()
    observer.schedule(NodeChangeHandler(server), path='.', recursive=True)
    observer.schedule(WorkflowChangeHandler(server), path='.', recursive=True)
    observer.schedule(LogWatcher(server), path='./logs', recursive=True)
    observer.start()

    # Initial system scan
    await server.scan_nodes()
    await server.scan_workflows()
    
    # Start WebSocket server
    async with websockets.serve(
        server.handle_client,
        "localhost",
        8765,
        ping_interval=None
    ):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())