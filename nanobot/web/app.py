"""FastAPI application for nanobot web channel."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from typing import Optional, TYPE_CHECKING
import json

from nanobot.web.database import init_database, close_database, get_database
from nanobot.web.schemas import HealthResponse
from nanobot.web.routes import conversations, messages, search

if TYPE_CHECKING:
    from nanobot.channels.web import WebChannel


# Store active WebSocket connections
class ConnectionManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.web_channel: Optional["WebChannel"] = None

    def set_web_channel(self, channel: "WebChannel"):
        """Set the WebChannel instance for handling messages."""
        self.web_channel = channel

    async def connect(self, session_id: str, websocket: WebSocket):
        """Connect a WebSocket client."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    async def disconnect(self, session_id: str):
        """Disconnect a WebSocket client."""
        if session_id in self.active_connections:
            websocket = self.active_connections.pop(session_id)
            # Actually close the WebSocket connection
            try:
                await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket {session_id}: {e}")
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_json(self, session_id: str, data: dict):
        """Send JSON data to a specific client."""
        if session_id not in self.active_connections:
            logger.warning(f"Session {session_id} not in active_connections")
            return False

        try:
            websocket = self.active_connections[session_id]
            # Check if WebSocket is still connected
            if websocket.client_state.name != "CONNECTED":
                logger.warning(f"WebSocket {session_id} is not connected (state: {websocket.client_state.name})")
                await self.disconnect(session_id)
                return False

            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Error sending to {session_id}: {e}")
            await self.disconnect(session_id)
            return False

    async def broadcast(self, data: dict, exclude: Optional[str] = None):
        """Broadcast data to all connected clients."""
        disconnected = []
        for session_id, ws in self.active_connections.items():
            if session_id != exclude:
                try:
                    await ws.send_json(data)
                except Exception as e:
                    logger.error(f"Error broadcasting to {session_id}: {e}")
                    disconnected.append(session_id)

        # Clean up disconnected clients
        for session_id in disconnected:
            await self.disconnect(session_id)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting nanobot web API...")

    # Initialize database if enabled
    from nanobot.config.loader import load_config
    try:
        config = load_config()
        if config.database.enabled:
            await init_database(
                host=config.database.host,
                port=config.database.port,
                user=config.database.user,
                password=config.database.password,
                db=config.database.database,
                pool_size=config.database.pool_size
            )
            logger.info("✓ Database initialized")
    except Exception as e:
        logger.warning(f"Could not initialize database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down nanobot web API...")
    await close_database()


# Create FastAPI app
def create_app(cors_origins: list[str] = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="nanobot Web API",
        description="Web API for nanobot AI assistant",
        version="0.1.0",
        lifespan=lifespan
    )

    # Configure CORS
    origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(conversations.router)
    app.include_router(messages.router)
    app.include_router(search.router)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        db = get_database()
        db_healthy = False
        if db:
            db_healthy = await db.health_check()

        return HealthResponse(
            status="healthy" if db_healthy else "degraded",
            database=db_healthy
        )

    @app.get("/status")
    async def get_status():
        """Get API and channel status."""
        return {
            "api": "running",
            "connections": len(manager.active_connections),
            "web_channel_enabled": manager.web_channel is not None
        }

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(
        websocket: WebSocket,
        session_id: str,
        token: Optional[str] = Query(None),
        user_id: Optional[str] = Query("anonymous")
    ):
        """
        WebSocket endpoint for real-time chat.

        The session_id serves as both the conversation identifier and WebSocket connection identifier.

        Query parameters:
        - token: Optional auth token (if configured)
        - user_id: User identifier (defaults to "anonymous")
        """
        # Accept the connection first (FastAPI requirement)
        await websocket.accept()
        logger.info(f"WebSocket connected: {session_id}")

        # Store the connection in manager
        manager.active_connections[session_id] = websocket

        try:
            # Delegate to WebChannel if available
            if manager.web_channel:
                # Don't call manager.connect() again - connection already accepted
                await manager.web_channel.handle_websocket(websocket, session_id, user_id or "anonymous")
            else:
                # Fallback to basic handler if WebChannel not set
                await _basic_websocket_handler(websocket, session_id)
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected normally: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {e}")
        finally:
            # Clean up connection
            await manager.disconnect(session_id)

    return app


# Create default app instance
app = create_app()


async def _basic_websocket_handler(websocket: WebSocket, session_id: str):
    """Basic WebSocket handler when WebChannel is not available."""
    await manager.connect(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "ping":
                await manager.send_json(session_id, {"type": "pong"})
            else:
                await manager.send_json(session_id, {
                    "type": "error",
                    "data": {"message": f"WebChannel not available. Unknown message type: {msg_type}"}
                })

    except WebSocketDisconnect:
        await manager.disconnect(session_id)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from {session_id}")
        await manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        await manager.disconnect(session_id)


# Helper function to send messages to WebSocket clients
async def send_to_websocket(session_id: str, message_type: str, data: dict) -> bool:
    """
    Send a message to a WebSocket client.

    Args:
        session_id: The session/conversation ID
        message_type: Type of message (e.g., 'message', 'title_generated', 'error')
        data: Message data

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        await manager.send_json(session_id, {"type": message_type, "data": data})
        return True
    except Exception as e:
        logger.error(f"Failed to send to {session_id}: {e}")
        return False


def set_cors_origins(origins: list[str]):
    """Update CORS origins for the app."""
    # This is a placeholder - in production, you'd want to recreate the middleware
    pass


__all__ = ["app", "manager", "send_to_websocket", "create_app"]
