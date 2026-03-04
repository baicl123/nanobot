"""Web channel implementation using FastAPI and WebSocket."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import TYPE_CHECKING

from loguru import logger
from fastapi import WebSocket
import uvicorn

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import WebConfig
from nanobot.web.app import create_app, manager, send_to_websocket
from nanobot.web.repositories.conversation_repo import ConversationRepository
from nanobot.web.repositories.message_repo import MessageRepository


class WebChannel(BaseChannel):
    """
    Web channel using FastAPI and WebSocket.

    Provides a web-based chat interface for nanobot.
    """

    name = "web"

    def __init__(
        self,
        config: WebConfig,
        bus: MessageBus,
    ):
        super().__init__(config, bus)
        self.config: WebConfig = config
        self._server_task: asyncio.Task | None = None
        self._uvicorn_server = None
        self._dispatch_task: asyncio.Task | None = None
        self._running = False

        # Create FastAPI app with configured CORS origins
        self.app = create_app(cors_origins=config.cors_origins)

        # Register this channel with the ConnectionManager
        manager.set_web_channel(self)

        # Store active WebSocket connections mapping
        # session_id -> {sender_id, conversation_id}
        self._connections: dict[str, dict] = {}

    async def start(self) -> None:
        """Start the FastAPI server and WebSocket handler."""
        if not self.config.enabled:
            logger.info("Web channel is disabled in config")
            return

        self._running = True

        # Start outbound dispatcher
        self._dispatch_task = asyncio.create_task(self._dispatch_outbound())

        # Configure uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info",
            access_log=False  # Disable access logs for cleaner output
        )
        self._uvicorn_server = uvicorn.Server(config)

        # Start the server in a background task
        self._server_task = asyncio.create_task(self._run_server())
        logger.info(f"Web channel server started on {self.config.host}:{self.config.port}")

        # Wait for server to start
        await asyncio.sleep(0.1)

        # Keep the channel running
        while self._running:
            await asyncio.sleep(1)

    async def _run_server(self) -> None:
        """Run the uvicorn server."""
        try:
            await self._uvicorn_server.serve()
        except asyncio.CancelledError:
            logger.info("Web channel server cancelled")
        except Exception as e:
            logger.error(f"Web channel server error: {e}")

    async def stop(self) -> None:
        """Stop the FastAPI server."""
        self._running = False

        # Stop dispatcher
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

        # Stop server
        if self._uvicorn_server:
            logger.info("Stopping web channel server...")
            self._uvicorn_server.should_exit = True
            if self._server_task:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass

        # Close all connections
        for session_id in list(self._connections.keys()):
            await self._close_connection(session_id)

        logger.info("Web channel stopped")

    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through the web channel.

        The chat_id is the conversation_id. We need to find the actual WebSocket session_id.
        """
        conversation_id = msg.chat_id

        # Find the actual session_id from self._connections
        # The manager.active_connections key is format: user_id:conversation_id
        # We need to find which connection has this conversation_id
        session_id = None
        for sess_id, conn_info in self._connections.items():
            if conn_info.get("conversation_id") == conversation_id:
                session_id = sess_id
                break

        if not session_id:
            logger.warning(f"No active connection found for conversation {conversation_id}")
            return

        # Check if session is connected in manager
        from nanobot.web.app import manager
        if session_id not in manager.active_connections:
            logger.warning(f"No active WebSocket connection for session {session_id}")
            return

        # Determine message type from metadata
        msg_type = msg.metadata.get("message_type", "message") if msg.metadata else "message"

        # Send message to WebSocket client
        await send_to_websocket(
            session_id=session_id,
            message_type=msg_type,
            data={
                "conversation_id": conversation_id,
                "content": msg.content,
                "role": "assistant",
                "timestamp": msg.metadata.get("timestamp") if msg.metadata else None
            }
        )

        # Only save final messages to database (not progress/thinking messages)
        if msg_type == "message" and self.config.persist_to_db:
            try:
                msg_repo = MessageRepository()
                # Clean metadata before saving (remove callback functions)
                clean_metadata = {}
                if msg.metadata:
                    for key, value in msg.metadata.items():
                        # Only include serializable values (not functions)
                        if not callable(value):
                            clean_metadata[key] = value

                await msg_repo.add(
                    conversation_id=msg.chat_id,
                    role="assistant",
                    content=msg.content,
                    metadata=clean_metadata
                )
            except Exception as e:
                logger.error(f"Failed to save message to database: {e}")

    async def send_thinking_start(self, session_id: str) -> None:
        """Send a signal to start the thinking state."""
        # Find the actual session_id (which is user_id:conversation_id)
        actual_session_id = self._find_session_id(session_id)
        if not actual_session_id:
            return

        from nanobot.web.app import manager
        if actual_session_id in manager.active_connections:
            logger.info(f"[Thinking] Sending thinking_start to {actual_session_id}")
            await send_to_websocket(
                session_id=actual_session_id,
                message_type="thinking_start",
                data={"status": "thinking"}
            )

    async def send_thinking_end(self, session_id: str) -> None:
        """Send a signal to end the thinking state."""
        # Find the actual session_id (which is user_id:conversation_id)
        actual_session_id = self._find_session_id(session_id)
        if not actual_session_id:
            return

        from nanobot.web.app import manager
        if actual_session_id in manager.active_connections:
            await send_to_websocket(
                session_id=actual_session_id,
                message_type="thinking_end",
                data={"status": "done"}
            )

    async def send_progress(self, session_id: str, content: str, tool_hint: bool = False) -> None:
        """Send a progress message during processing."""
        # Find the actual session_id (which is user_id:conversation_id)
        actual_session_id = self._find_session_id(session_id)
        if not actual_session_id:
            return

        from nanobot.web.app import manager
        if actual_session_id in manager.active_connections:
            logger.info(f"[Thinking] Sending progress to {actual_session_id}: {content[:50]}")
            await send_to_websocket(
                session_id=actual_session_id,
                message_type="progress",
                data={"content": content, "tool_hint": tool_hint}
            )

    def _find_session_id(self, session_or_conversation_id: str) -> str | None:
        """
        Find the actual session_id (user_id:conversation_id) from conversation_id or session_id.

        Args:
            session_or_conversation_id: Can be either:
                - conversation_id (e.g., "1772413766214")
                - session_id (e.g., "60079031:1772413766214")

        Returns:
            The actual session_id (key in self._connections), or None if not found
        """
        # If it's already a session_id (contains ':'), check directly
        if ':' in session_or_conversation_id:
            # It's a session_id, check if it exists in connections
            if session_or_conversation_id in self._connections:
                return session_or_conversation_id

            # Extract conversation_id and try to match
            parts = session_or_conversation_id.split(':', 1)
            conversation_id = parts[1]
        else:
            # It's a conversation_id
            conversation_id = session_or_conversation_id

        # Search by conversation_id
        for sess_id, conn_info in self._connections.items():
            if conn_info.get("conversation_id") == conversation_id:
                return sess_id

        logger.warning(f"No connection found for {session_or_conversation_id}")
        return None

    async def handle_websocket(self, websocket: WebSocket, session_id: str, user_id: str = "anonymous") -> None:
        """
        Handle a WebSocket connection with two-tier memory support.

        Session Key format: web:{user_id}:{session_id}
        - user_id: For UserMemory (cross-session long-term memory)
        - session_id: For SessionMemory (single-session short-term memory)
        - Single active session: Close old connection when new one connects for same user

        Note: The WebSocket connection is already accepted by FastAPI before this method is called.
        """
        # Check auth token if configured
        if self.config.auth_token:
            # Token validation should be done here
            # For now, we'll accept all connections
            pass

        # Check connection limit using manager's active connections
        from nanobot.web.app import manager
        if len(manager.active_connections) >= self.config.max_connections:
            await websocket.close(code=1008, reason="Max connections reached")
            return

        # Check if user is allowed
        if not self.is_allowed(user_id):
            await websocket.close(code=1003, reason="Access denied")
            logger.warning(f"Access denied for user {user_id}")
            return

        # Parse session_id: might be in format "user123:conv-001" or just "conv-001"
        parts = session_id.split(':', 1)
        if len(parts) == 2:
            conversation_id = parts[1]
            # Validate user_id matches
            if user_id != parts[0]:
                logger.warning(f"User ID mismatch: {user_id} != {parts[0]}")
                await websocket.close(code=1008, reason="Invalid user ID")
                return
        else:
            # Fallback: use session_id as conversation_id
            conversation_id = session_id

        # Validate conversation_id
        if not conversation_id or conversation_id == "null" or conversation_id.strip() == "":
            logger.warning(f"Invalid conversation_id: {conversation_id}")
            await websocket.close(code=1008, reason="Invalid conversation ID")
            return

        # Session key for two-tier memory
        session_key = f"web:{user_id}:{conversation_id}"

        # Single active session: Close old connection for this user (but different conversation)
        for old_session_id, conn_info in list(self._connections.items()):
            # Check if same user (not same conversation)
            if conn_info.get("user_id") == user_id and conn_info.get("conversation_id") != conversation_id:
                logger.info(f"Closing old connection for user {user_id}: {old_session_id}")
                # Close old WebSocket connection
                await manager.disconnect(old_session_id)
                await self._close_connection(old_session_id)

        # Get or create conversation
        conv_repo = ConversationRepository()

        # Check if conversation exists, if not create it
        conv_exists = await conv_repo.exists(conversation_id)
        if not conv_exists:
            try:
                await conv_repo.create(
                    user_id=user_id,
                    title="新对话",
                    channel="web",
                    conv_id=conversation_id
                )
                logger.debug(f"Created conversation {conversation_id} for user {user_id}")
            except Exception as e:
                # Handle duplicate key error - conversation might have been created by another connection
                error_code = getattr(e, 'args', [None])[0] if e.args else None
                if error_code == 1062:  # Duplicate entry
                    logger.debug(f"Conversation {conversation_id} already exists, created by another connection")
                    # Verify it now exists
                    if not await conv_repo.exists(conversation_id):
                        raise  # If it still doesn't exist, this is a real error
                else:
                    raise  # Re-raise other errors

        # Store connection info
        self._connections[session_id] = {
            "sender_id": user_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_key": session_key
        }

        logger.info(f"WebSocket connection established: session_key={session_key}, user={user_id}, conv={conversation_id}")

        # Send connection confirmation
        try:
            await send_to_websocket(
                session_id=session_id,
                message_type="connected",
                data={
                    "session_id": session_id,
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "session_key": session_key
                }
            )
        except Exception as e:
            logger.error(f"Error sending connected message: {e}")
            # Don't return - continue to message loop even if connected message fails

        try:
            # Message loop
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                msg_type = message.get("type")

                if msg_type == "ping":
                    # Heartbeat/ping
                    await send_to_websocket(session_id, "pong", {})

                elif msg_type == "message":
                    # Chat message
                    content = message.get("data", {}).get("content", "")
                    if not content:
                        continue

                    # Save user message to database if enabled
                    if self.config.persist_to_db:
                        try:
                            msg_repo = MessageRepository()
                            await msg_repo.add(
                                conversation_id=conversation_id,
                                role="user",
                                content=content
                            )
                            await conv_repo.increment_count(conversation_id)
                        except Exception as e:
                            logger.error(f"Failed to save message to database: {e}")

                    # Create async callbacks for real-time progress
                    async def on_thinking_start():
                        await self.send_thinking_start(session_id)

                    async def on_thinking_end():
                        await self.send_thinking_end(session_id)

                    async def on_progress(content: str, tool_hint: bool = False):
                        await self.send_progress(session_id, content, tool_hint=tool_hint)

                    # Forward to message bus for agent processing
                    # Pass WebSocket-specific callbacks for real-time progress
                    await self._handle_message(
                        sender_id=user_id,
                        chat_id=conversation_id,
                        content=content,
                        session_key=session_key,  # Use the new session_key format: web:{user_id}:{session_id}
                        metadata={
                            "user_id": user_id,  # CRITICAL: for UserMemory
                            "session_id": conversation_id,  # CRITICAL: for SessionMemory
                            "channel": "web",
                            "on_thinking_start": on_thinking_start,
                            "on_thinking_end": on_thinking_end,
                            "on_progress": on_progress
                        }
                    )

                elif msg_type == "get_history":
                    # Send conversation history
                    if self.config.enable_history_api:
                        await self._send_history(conversation_id, session_id)

                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await send_to_websocket(
                        session_id,
                        "error",
                        {"message": f"Unknown message type: {msg_type}"}
                    )

        except Exception as e:
            if "disconnect" not in str(e).lower():
                logger.error(f"WebSocket error for {session_id}: {e}")
        finally:
            await self._close_connection(session_id)

    async def _send_history(self, conversation_id: str, session_id: str) -> None:
        """Send conversation history to the client."""
        try:
            msg_repo = MessageRepository()
            messages = await msg_repo.get_by_conversation(conversation_id, limit=100)

            await send_to_websocket(
                session_id,
                "history",
                {"conversation_id": conversation_id, "messages": messages}
            )
        except Exception as e:
            logger.error(f"Failed to send history: {e}")
            await send_to_websocket(
                session_id,
                "error",
                {"message": "Failed to load history"}
            )

    async def _close_connection(self, session_id: str) -> None:
        """Close a WebSocket connection and clean up."""
        from nanobot.web.app import manager

        # Clean up local metadata
        if session_id in self._connections:
            del self._connections[session_id]

        # Also disconnect from manager if it's still there
        if session_id in manager.active_connections:
            await manager.disconnect(session_id)

        logger.info(f"WebSocket connection closed: {session_id}")

    async def _dispatch_outbound(self) -> None:
        """Dispatch outbound messages from the bus to WebSocket clients."""
        logger.info("Web channel outbound dispatcher started")

        while self._running:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_outbound(),
                    timeout=1.0
                )

                # Only handle messages for this channel
                if msg.channel != self.name:
                    continue

                await self.send(msg)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in outbound dispatcher: {e}")


# Update the FastAPI app's WebSocket endpoint to use WebChannel
async def websocket_handler(websocket: WebSocket, session_id: str):
    """WebSocket handler that delegates to WebChannel."""
    # This is a placeholder - the actual handler will be set up when the channel starts
    # For now, we'll use the basic handler from app.py
    pass
