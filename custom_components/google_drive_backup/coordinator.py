"""WebSocket coordinator for Google Drive Backup integration."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers import dispatcher
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)

DOMAIN = "google_drive_backup"

RECONNECT_DELAY = 60  # seconds
PING_INTERVAL = 30  # seconds
PING_TIMEOUT = 10  # seconds


class GoogleDriveBackupCoordinator:
    """Manage WebSocket connection to Google Drive Backup addon."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.host = host
        self.port = port
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._running = False
        self._task: asyncio.Task | None = None
        self._ever_connected = False

        # State storage
        self._backup_state: dict[str, Any] = {"state": "unknown", "attributes": {}}
        self._backup_stale = False
        self._connected = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for all entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, "hassio_google_drive_backup")},
            name="Google Drive Backup",
            manufacturer="Home Assistant Community",
            model="Add-on Integration",
            configuration_url="http://homeassistant.local:8099",
        )

    @property
    def connected(self) -> bool:
        """Return if we're connected to the addon."""
        return self._connected

    @property
    def backup_state(self) -> dict[str, Any]:
        """Get the current backup state."""
        return self._backup_state

    @property
    def backup_stale(self) -> bool:
        """Get the backup stale status."""
        return self._backup_stale

    async def async_start(self) -> None:
        """Start the coordinator."""
        if self._running:
            return
        
        self._running = True
        self._session = aiohttp.ClientSession()
        self._task = asyncio.create_task(self._run())
        _LOGGER.info("Google Drive Backup coordinator started")

    async def async_stop(self) -> None:
        """Stop the coordinator."""
        self._running = False
        
        if self._ws and not self._ws.closed:
            await self._ws.close()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._session:
            await self._session.close()
        
        _LOGGER.info("Google Drive Backup coordinator stopped")

    async def _run(self) -> None:
        """Main coordinator loop."""
        while self._running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Unexpected error in coordinator: %s", err, exc_info=True)
            
            if self._running:
                # Mark as disconnected and notify sensors
                if self._connected:
                    self._connected = False
                    self._notify_availability_changed()
                
                if self._ever_connected:
                    _LOGGER.info("Reconnecting to addon in %s seconds...", RECONNECT_DELAY)
                else:
                    _LOGGER.debug("Addon unavailable, will retry in %s seconds...", RECONNECT_DELAY)
                await asyncio.sleep(RECONNECT_DELAY)

    async def _connect_and_listen(self) -> None:
        """Connect to WebSocket and listen for messages."""
        url = f"http://{self.host}:{self.port}/ws"
        if self._ever_connected:
            _LOGGER.info("Attempting to connect to Google Drive Backup addon at %s", url)
        else:
            _LOGGER.debug("Attempting to connect to Google Drive Backup addon at %s", url)
        
        try:
            async with self._session.ws_connect(
                url,
                heartbeat=PING_INTERVAL,
                timeout=aiohttp.ClientTimeout(total=PING_TIMEOUT),
            ) as ws:
                self._ws = ws
                self._connected = True
                self._ever_connected = True
                self._notify_availability_changed()
                _LOGGER.info("Successfully connected to Google Drive Backup addon WebSocket")
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        _LOGGER.debug("Received message: %s", msg.data[:100])  # Log first 100 chars
                        await self._handle_message(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error("WebSocket error: %s", ws.exception())
                        break
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                        _LOGGER.info("WebSocket connection closed by server")
                        break
        
        except aiohttp.ClientError as err:
            if self._ever_connected:
                _LOGGER.warning("Connection error to %s: %s", url, err)
            else:
                _LOGGER.debug("Addon not yet reachable at %s: %s", url, err)
        except asyncio.TimeoutError:
            if self._ever_connected:
                _LOGGER.warning("Connection timeout to %s", url)
            else:
                _LOGGER.debug("Addon not yet reachable at %s (timeout)", url)
        except Exception as err:
            _LOGGER.error("Unexpected error connecting to %s: %s", url, err, exc_info=True)
        finally:
            self._ws = None
            if self._connected:
                _LOGGER.info("Disconnected from Google Drive Backup addon")
                self._connected = False
                self._notify_availability_changed()

    async def _handle_message(self, data: str) -> None:
        """Handle incoming WebSocket message."""
        try:
            message = json.loads(data)
            msg_type = message.get("type")
            
            if msg_type == "backup_state":
                self._backup_state = {
                    "state": message.get("state", "unknown"),
                    "attributes": message.get("attributes", {})
                }
                dispatcher.async_dispatcher_send(
                    self.hass, f"{DOMAIN}_update_backup"
                )
                _LOGGER.debug("Updated backup state: %s", self._backup_state["state"])
            
            elif msg_type == "backup_stale":
                self._backup_stale = message.get("is_stale", False)
                dispatcher.async_dispatcher_send(
                    self.hass, f"{DOMAIN}_update_stale"
                )
                _LOGGER.debug("Updated backup stale: %s", self._backup_stale)
            
            else:
                _LOGGER.warning("Unknown message type: %s", msg_type)
        
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to decode message: %s", err)
        except Exception as err:
            _LOGGER.error("Error handling message: %s", err, exc_info=True)

    def _notify_availability_changed(self) -> None:
        """Notify all sensors about availability change."""
        dispatcher.async_dispatcher_send(
            self.hass, f"{DOMAIN}_availability_changed"
        )
        _LOGGER.debug("Availability changed: connected=%s", self._connected)
