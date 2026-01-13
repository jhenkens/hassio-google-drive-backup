"""WebSocket server for pushing state updates to Home Assistant integration."""
import asyncio
import json
from typing import Set, Dict, Any
from aiohttp import web
from injector import singleton, inject

from ..time import Time
from ..config import Config, Setting, Startable
from ..logger import getLogger

logger = getLogger(__name__)


@singleton
class IntegrationWebSocketServer(Startable):
    """WebSocket server for communicating with the Home Assistant integration."""

    @inject
    def __init__(self, config: Config, time: Time):
        """Initialize the WebSocket server."""
        self._config = config
        self._time = time
        self._clients: Set[web.WebSocketResponse] = set()
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._running = False
        self._last_backup_state: Dict[str, Any] | None = None
        self._last_backup_stale: Dict[str, Any] | None = None

    async def start(self) -> None:
        """Start the WebSocket server."""
        if self._running:
            return

        port = self._config.get(Setting.INTEGRATION_WS_PORT) 
        
        self._app = web.Application()
        self._app.router.add_get('/ws', self._websocket_handler)
        self._app.router.add_get('/health', self._health_handler)
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        self._site = web.TCPSite(self._runner, '0.0.0.0', port)
        await self._site.start()
        
        self._running = True
        logger.info(f"Integration WebSocket server started on port {port}")

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self._running:
            return

        # Close all client connections
        for ws in list(self._clients):
            await ws.close()
        self._clients.clear()

        if self._site:
            await self._site.stop()
        
        if self._runner:
            await self._runner.cleanup()
        
        self._running = False
        logger.info("Integration WebSocket server stopped")

    async def _health_handler(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        return web.Response(text=json.dumps({
            "status": "ok",
            "clients": len(self._clients)
        }), content_type="application/json")

    async def _websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)
        
        self._clients.add(ws)
        client_id = id(ws)
        remote = request.remote
        logger.info(f"Integration client connected from {remote} (id: {client_id}). Total clients: {len(self._clients)}")
        logger.debug(f"Client connection details - Headers: {dict(request.headers)}")
        
        # Send latest state to the newly connected client
        if self._last_backup_state:
            try:
                await ws.send_str(json.dumps(self._last_backup_state))
                logger.debug(f"Sent latest backup_state to new client {client_id}")
            except Exception as e:
                logger.error(f"Error sending latest backup_state to client {client_id}: {e}")
        
        if self._last_backup_stale:
            try:
                await ws.send_str(json.dumps(self._last_backup_stale))
                logger.debug(f"Sent latest backup_stale to new client {client_id}")
            except Exception as e:
                logger.error(f"Error sending latest backup_stale to client {client_id}: {e}")
        
        try:
            async for msg in ws:
                # We don't expect messages from the integration, but handle them gracefully
                if msg.type == web.WSMsgType.TEXT:
                    logger.debug(f"Received message from client {client_id}: {msg.data}")
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error from client {client_id}: {ws.exception()}")
        except Exception as e:
            logger.error(f"Exception in WebSocket handler for client {client_id}: {e}", exc_info=True)
        finally:
            self._clients.discard(ws)
            logger.info(f"Integration client disconnected (id: {client_id}). Total clients: {len(self._clients)}")
        
        return ws

    async def send_backup_state(self, state: str, attributes: Dict[str, Any]) -> None:
        """Send backup state update to all connected clients."""
        message = {
            "type": "backup_state",
            "state": state,
            "attributes": attributes
        }
        self._last_backup_state = message
        await self._broadcast(message)

    async def send_backup_stale(self, is_stale: bool) -> None:
        """Send backup stale status to all connected clients."""
        message = {
            "type": "backup_stale",
            "is_stale": is_stale
        }
        self._last_backup_stale = message
        await self._broadcast(message)

    async def _broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        if not self._clients:
            logger.debug(f"No integration clients connected, skipping broadcast of {message.get('type')}")
            return

        logger.debug(f"Broadcasting {message.get('type')} to {len(self._clients)} clients")
        message_str = json.dumps(message)
        disconnected = set()
        
        for ws in self._clients:
            try:
                if ws.closed:
                    disconnected.add(ws)
                else:
                    await ws.send_str(message_str)
            except Exception as e:
                logger.error(f"Error sending to client {id(ws)}: {e}")
                disconnected.add(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self._clients.discard(ws)
        
        if disconnected:
            logger.debug(f"Removed {len(disconnected)} disconnected clients")

    @property
    def has_clients(self) -> bool:
        """Return True if there are connected clients."""
        return len(self._clients) > 0

    @property
    def client_count(self) -> int:
        """Return the number of connected clients."""
        return len(self._clients)
