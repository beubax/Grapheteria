from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from fastapi.requests import Request
import os
import uvicorn
from watchdog.observers import Observer
from grapheteria.server.workflow_manager import WorkflowManager
from grapheteria.server.handlers.file_handlers import NodeChangeHandler, WorkflowChangeHandler
from grapheteria.server.routes import router as api_router
# Create WorkflowManager instance
workflow_manager = WorkflowManager()

# Configure file system watchers
observer = Observer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    watch_dir = os.environ.get('WORKFLOW_WATCH_DIR', '.')
    observer.schedule(NodeChangeHandler(workflow_manager), path=watch_dir, recursive=True)
    observer.schedule(WorkflowChangeHandler(workflow_manager), path=watch_dir, recursive=True)
    observer.start()
    workflow_manager.setup_node_registry()
    
    workflow_manager.scan_nodes()
    workflow_manager.scan_workflows()
    
    yield

    observer.stop()
    observer.join()

# Create FastAPI app
app = FastAPI(title="Workflow Server", lifespan=lifespan)

# API routes
app.include_router(api_router, prefix="/api")

# Set up templates
package_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(package_dir, "static", "ui")
templates = Jinja2Templates(directory=static_dir)

# Serve index.html using templates
@app.get("/ui/")
async def get_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Serve assets with explicit MIME type handling
@app.get("/assets/{file_path:path}")
async def get_asset(file_path: str):
    assets_dir = os.path.join(static_dir, "assets")
    file_path = os.path.join(assets_dir, file_path)
    
    if os.path.exists(file_path) and file_path.endswith(".js"):
        return FileResponse(file_path, media_type="application/javascript")
    return FileResponse(file_path)

# Redirect from root to /ui/
@app.get("/")
async def redirect_to_ui():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    # Accept all WebSocket connections without origin checks
    await websocket.accept()
    await workflow_manager.register(websocket)
    
    try:
        while True:
            message = await websocket.receive_text()
            await workflow_manager.handle_client_message(websocket, message)
    except WebSocketDisconnect:
        pass
    finally:
        await workflow_manager.unregister(websocket)

def run_server():
    """Run just the backend server"""
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host=host, port=port)

def run_app():
    """Run the complete application with backend and UI"""
    # Set environment variable to indicate we're running the full app
    os.environ["WORKFLOW_APP_MODE"] = "full"
    
    # We're using the same function, but might add additional setup in the future
    run_server()

if __name__ == "__main__":
    run_server()