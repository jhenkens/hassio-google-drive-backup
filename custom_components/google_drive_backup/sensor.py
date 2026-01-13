"""Sensor platform for Google Drive Backup integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers import dispatcher

from .coordinator import GoogleDriveBackupCoordinator

_LOGGER = logging.getLogger(__name__)

DOMAIN = "google_drive_backup"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Google Drive Backup sensor platform."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([BackupStateSensor(coordinator)])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Google Drive Backup sensors from a config entry."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([BackupStateSensor(coordinator)])


class BackupStateSensor(SensorEntity):
    """Representation of the Backup State sensor."""

    _attr_name = "Backup State"
    _attr_unique_id = "hassio_google_drive_backup.backup_state"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:cloud-upload"
    _attr_should_poll = False

    def __init__(self, coordinator: GoogleDriveBackupCoordinator) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._attr_device_info = coordinator.device_info

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        @callback
        def update_state() -> None:
            """Update the sensor state."""
            self.async_write_ha_state()

        @callback
        def update_availability() -> None:
            """Update the sensor availability."""
            self.async_write_ha_state()

        self.async_on_remove(
            dispatcher.async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update_backup", update_state
            )
        )
        self.async_on_remove(
            dispatcher.async_dispatcher_connect(
                self.hass, f"{DOMAIN}_availability_changed", update_availability
            )
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.connected

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._coordinator.backup_state.get("state", "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._coordinator.backup_state.get("attributes", {})



