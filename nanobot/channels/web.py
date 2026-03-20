"""Web channel implementation for nanobot."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Set
from datetime import datetime

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import WebConfig
from nanobot.web.db import init_db, get_session_meta, create_session, update_session, delete_session, list_user_sessions
from nanobot.web.models import SessionMeta


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str
    data: Dict[str, Any]


class WebChannel(BaseChannel):
    """
    Web channel implementation using FastAPI and WebSocket.

    Provides web-based chat interface with support for multiple users and sessions.
    """

    name = "web"

    def __init__(self, config: WebConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: WebConfig = config

        # Initialize database
        init_db()

        # WebSocket connections: {user_id: set(websocket)}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Create FastAPI app
        self.app = FastAPI(title="nanobot Web Channel")

        # Configure CORS
        if self.config.cors_origins:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Register routes
        self._register_routes()

        # Mount static files if they exist
        static_path = Path(__file__).parent.parent / "web" / "static"
        if static_path.exists():
            self.app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

        # Server task
        self._server_task: asyncio.Task | None = None

    def _register_routes(self) -> None:
        """Register FastAPI routes."""

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, empId: str, deptname: str = ""):
            """WebSocket endpoint for real-time communication."""
            # Validate user permissions
            if not self.is_allowed(empId):
                await websocket.close(code=403, reason="Access denied")
                return

            await websocket.accept()

            # Add to active connections
            if empId not in self.active_connections:
                self.active_connections[empId] = set()
            self.active_connections[empId].add(websocket)

            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        msg = WebSocketMessage(**json.loads(data))
                        await self._handle_websocket_message(empId, deptname, msg, websocket)
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "data": {"message": str(e)}
                        }))

            except WebSocketDisconnect:
                # Remove from active connections
                if empId in self.active_connections:
                    self.active_connections[empId].discard(websocket)
                    if not self.active_connections[empId]:
                        del self.active_connections[empId]

        @self.app.get("/api/sessions")
        async def get_user_sessions(empId: str):
            """Get all sessions for a user."""
            if not self.is_allowed(empId):
                raise HTTPException(status_code=403, detail="Access denied")
            sessions = list_user_sessions(empId)
            return {"sessions": [s.model_dump() for s in sessions]}

        @self.app.post("/api/sessions")
        async def create_new_session(empId: str, name: str = "New Chat"):
            """Create a new session for a user."""
            if not self.is_allowed(empId):
                raise HTTPException(status_code=403, detail="Access denied")
            session_id = f"web:{empId}:{uuid.uuid4()}"
            session = SessionMeta(
                session_id=session_id,
                user_id=empId,
                name=name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_message="",
            )
            create_session(session)
            return {"session": session.model_dump()}

        @self.app.put("/api/sessions/{session_id}")
        async def update_session_name(session_id: str, empId: str, name: str):
            """Update session name."""
            if not self.is_allowed(empId):
                raise HTTPException(status_code=403, detail="Access denied")
            session = get_session_meta(session_id)
            if not session or session.user_id != empId:
                raise HTTPException(status_code=404, detail="Session not found")
            session.name = name
            update_session(session)
            return {"session": session.model_dump()}

        @self.app.delete("/api/sessions/{session_id}")
        async def delete_user_session(session_id: str, empId: str):
            """Delete a session."""
            if not self.is_allowed(empId):
                raise HTTPException(status_code=403, detail="Access denied")
            session = get_session_meta(session_id)
            if not session or session.user_id != empId:
                raise HTTPException(status_code=404, detail="Session not found")
            delete_session(session_id)
            return {"success": True}

        @self.app.get("/api/sessions/{session_id}/messages")
        async def get_session_messages(session_id: str, empId: str):
            """Get historical messages for a session."""
            if not self.is_allowed(empId):
                raise HTTPException(status_code=403, detail="Access denied")
            session = get_session_meta(session_id)
            if not session or session.user_id != empId:
                raise HTTPException(status_code=404, detail="Session not found")

            # 解析session_id获取uuid
            try:
                _, user_id, session_uuid = session_id.split(":", 2)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session ID format")

            # 构建消息文件路径
            from nanobot.config.paths import get_workspace_path
            session_file = get_workspace_path() / "sessions" / f"web_{user_id}_{session_uuid}.jsonl"

            messages = []
            if session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                msg = json.loads(line)
                                # 过滤掉中间过程消息：流式片段、工具调用提示、错误信息等
                                metadata = msg.get("metadata", {})
                                if metadata.get("_progress") or metadata.get("_tool_hint") or metadata.get("_is_error"):
                                    continue
                                # 只保留用户和助手的最终消息
                                role = msg.get("role")
                                if role not in ["user", "assistant"]:
                                    continue
                                # 过滤掉空内容
                                content = msg.get("content", "").strip()
                                if not content:
                                    continue
                                # 只保留需要的字段
                                messages.append({
                                    "role": role,
                                    "content": content,
                                    "created_at": msg.get("created_at")
                                })
                            except json.JSONDecodeError:
                                continue

            return {"messages": messages}

    async def _handle_websocket_message(self, empId: str, deptname: str, msg: WebSocketMessage, websocket: WebSocket) -> None:
        """Handle incoming WebSocket message."""
        if msg.type == "message":
            # Chat message from user
            content = msg.data.get("content", "")
            session_id = msg.data.get("session_id")

            if not content or not session_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Missing content or session_id"}
                }))
                return

            # Validate session belongs to user
            session = get_session_meta(session_id)
            if not session or session.user_id != empId:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid session"}
                }))
                return

            # Update session metadata
            session.updated_at = datetime.utcnow()
            session.last_message = content[:100]  # Truncate for preview
            update_session(session)

            # Prepare metadata with user info
            metadata = {
                "emp_id": empId,
                "deptname": deptname,
                "session_id": session_id,
            }

            # Override session key to ensure user isolation
            session_key = f"web:{empId}:{session_id.split(':')[-1]}"

            # Forward to message bus
            await self._handle_message(
                sender_id=empId,
                chat_id=session_id,
                content=content,
                metadata=metadata,
                session_key=session_key,
            )

        elif msg.type == "ping":
            # Heartbeat
            await websocket.send_text(json.dumps({"type": "pong", "data": {}}))

        else:
            logger.warning(f"Unknown WebSocket message type: {msg.type}")

    async def start(self) -> None:
        """Start the web server."""
        self._running = True
        logger.info(f"Starting web channel server on {self.config.host}:{self.config.port}")

        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())

        try:
            await self._server_task
        except asyncio.CancelledError:
            logger.info("Web server task cancelled")
        finally:
            self._running = False

    async def stop(self) -> None:
        """Stop the web server and clean up connections."""
        self._running = False

        # Close all WebSocket connections
        for user_id, connections in self.active_connections.items():
            for ws in connections:
                try:
                    await ws.close(code=1001, reason="Server shutting down")
                except Exception as e:
                    logger.debug(f"Error closing WebSocket connection: {e}")
        self.active_connections.clear()

        # Cancel server task
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass

        logger.info("Web channel stopped")

    async def send(self, msg: OutboundMessage) -> None:
        """Send an outbound message to the appropriate user."""
        # Extract user ID from chat ID (format: web:{user_id}:{uuid})
        try:
            _, user_id, _ = msg.chat_id.split(":", 2)
        except ValueError:
            logger.error(f"Invalid chat_id format for web channel: {msg.chat_id}")
            return

        # Get all active connections for the user
        connections = self.active_connections.get(user_id, set())
        if not connections:
            logger.debug(f"No active connections for user {user_id}, message dropped")
            return

        # Prepare message payload
        payload = {
            "type": "message",
            "data": {
                "session_id": msg.chat_id,
                "content": msg.content,
                "role": "assistant",
                "metadata": msg.metadata,
                "is_progress": msg.metadata.get("_progress", False),
                "is_tool_hint": msg.metadata.get("_tool_hint", False),
            }
        }

        # Send to all active connections for the user
        for ws in connections:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
