"""FastAPI app for web channel.

This file is provided for running the web channel separately if needed.
In normal operation, the web channel is managed by the ChannelManager.
"""

from fastapi import FastAPI
from nanobot.web.dependencies import get_current_user, get_current_user_ws
from nanobot.web.db import init_db

# Initialize database
init_db()

app = FastAPI(title="nanobot Web Channel")

# Import routes
# Note: In normal operation, routes are registered in the WebChannel class
# This file is for standalone usage only

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18791)
