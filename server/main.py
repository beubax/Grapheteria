from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from watchdog.observers import Observer
from server.workflow_manager import WorkflowManager
from server.handlers.file_handlers import NodeChangeHandler, WorkflowChangeHandler
from server.routes import router as api_router

# Create WorkflowManager instance
workflow_manager = WorkflowManager()

# Configure file system watchers
observer = Observer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    observer.schedule(NodeChangeHandler(workflow_manager), path='.', recursive=True)
    observer.schedule(WorkflowChangeHandler(workflow_manager), path='.', recursive=True)
    observer.start()
    
    # Initial system scan
    workflow_manager.scan_nodes()
    workflow_manager.scan_workflows()

    yield

    observer.stop()
    observer.join()

# Create FastAPI application
app = FastAPI(title="Workflow Server", lifespan=lifespan)
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)    

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    # Accept all WebSocket connections without origin checks
    await websocket.accept()
    await workflow_manager.register(websocket)
    
    try:
        while True:
            message = await websocket.receive_text()
            print(f"Received message: {message}")
            await workflow_manager.handle_client_message(websocket, message)
    except WebSocketDisconnect:
        pass
    finally:
        await workflow_manager.unregister(websocket)



if __name__ == "__main__":
    uvicorn.run("server.main:app", host="localhost", port=8765, log_level="info")