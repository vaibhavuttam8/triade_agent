import uvicorn
from .api import app
import asyncio
from .context_manager import context_manager
import signal
import sys

async def cleanup_task():
    """Periodic task to clean up old contexts"""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        context_manager.cleanup_old_contexts()

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    sys.exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start the cleanup task
    loop.create_task(cleanup_task())
    
    # Run the application
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        loop=loop
    )
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())

if __name__ == "__main__":
    main() 