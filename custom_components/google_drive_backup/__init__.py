"""The Google Drive Backup integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .coordinator import GoogleDriveBackupCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "google_drive_backup"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Default configuration - use addon slug as hostname for local communication
DEFAULT_HOST = "eab5354b-hassio-google-drive-backup"
DEFAULT_PORT = 8100


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Google Drive Backup integration from YAML."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Google Drive Backup from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    
    coordinator = GoogleDriveBackupCoordinator(hass, host, port)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = coordinator
    
    # Start the coordinator
    await coordinator.async_start()
    
    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop("coordinator", None)
        if coordinator:
            await coordinator.async_stop()
    
    return unload_ok
