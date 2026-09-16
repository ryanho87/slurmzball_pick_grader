"""
Main application file for the Fantasy Roast Bot API
"""

from fastapi import FastAPI
from config import config_manager, ConfigWatcher
from endpoints import router

# Create FastAPI application
app = FastAPI(title="Fantasy Roast Bot (Python)")

# Include all endpoints from the router
app.include_router(router)

# Global config watcher instance
config_watcher = None


@app.on_event("startup")
async def startup_event():
    """Start configuration file watcher on startup"""
    global config_watcher
    
    # Start config watcher for automatic reloading
    config_watcher = ConfigWatcher("config/base.yaml", config_manager.reload_configuration)
    config_watcher.start()
    print("🚀 Configuration file watcher started")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop configuration file watcher on shutdown"""
    global config_watcher
    
    if config_watcher:
        config_watcher.stop()
        print("🛑 Configuration file watcher stopped")


# For development/testing - if running this file directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)