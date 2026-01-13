"""Binary sensor platform for Google Drive Backup integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up the Google Drive Backup binary sensor platform."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([BackupStaleSensor(coordinator)])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Google Drive Backup binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([BackupStaleSensor(coordinator)])


class BackupStaleSensor(BinarySensorEntity):
    """Representation of the Backup Stale binary sensor."""

    _attr_name = "Backup Stale"
    _attr_unique_id = "hassio_google_drive_backup.backup_stale"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"
    _attr_should_poll = False

    def __init__(self, coordinator: GoogleDriveBackupCoordinator) -> None:
        """Initialize the binary sensor."""
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
                self.hass, f"{DOMAIN}_update_stale", update_state
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
    def is_on(self) -> bool:
        """Return true if the backup is stale."""
        return self._coordinator.backup_stale
