# Google Drive Backup Integration

This is a Home Assistant custom integration that pairs with the Google Drive Backup addon. It provides efficient state management for backup sensors using a **WebSocket-based local push architecture**.

## Features

- **Backup State Sensor** (`sensor.backup_state`): Shows the current backup state with detailed attributes
- **Snapshot State Sensor** (`sensor.snapshot_state`): Legacy sensor for backward compatibility
- **Backup Stale Binary Sensor** (`binary_sensor.backup_stale`): Indicates if backups are stale/outdated
- **WebSocket-based updates**: Real-time push updates from the addon via local WebSocket connection
- **Automatic availability tracking**: Sensors show as "unavailable" when WebSocket is disconnected
- **Auto-discovery**: Automatically connects to the addon without manual configuration

## Architecture

This integration uses a **WebSocket push architecture** for optimal efficiency:

1. The addon runs a WebSocket server on port 8099
2. The integration connects as a WebSocket client
3. The addon pushes state updates through the WebSocket in real-time
4. When disconnected, sensors automatically show as "unavailable"
5. The integration automatically reconnects if the connection is lost

This approach provides:
- **Real-time updates** with zero polling overhead
- **Proper availability tracking** - sensors show unavailable when addon is down
- **Local communication only** - no external dependencies
- **Better performance** than REST API polling
- **Fallback support** - addon can still use REST API if integration isn't installed

## Installation

### Manual Installation

1. Copy the `custom_components/google_drive_backup` folder to your Home Assistant's `config/custom_components/` directory
2. Restart Home Assistant
3. The integration will automatically start and connect to the addon

Your directory structure should look like:
```
config/
├── custom_components/
│   └── google_drive_backup/
│       ├── __init__.py
│       ├── manifest.json
│       ├── coordinator.py
│       ├── sensor.py
│       └── binary_sensor.py
```

### HACS Installation (Future)

This integration can be added to HACS in the future for easier installation and updates.

## Configuration

**No configuration required!** The integration:
- Automatically discovers and connects to the addon
- Uses default connection settings (localhost:8099)
- Starts immediately when Home Assistant loads
- Reconnects automatically if the connection is lost

## Sensors

### Backup State Sensor

**Entity ID:** `sensor.backup_state`

**States:**
- `waiting`: Waiting for next backup
- `backed_up`: Backups are current
- `error`: Backups are stale or an error occurred
- `unavailable`: Cannot connect to addon (WebSocket disconnected)

**Attributes:**
- `last_backup`: ISO timestamp of the last backup
- `next_backup`: ISO timestamp of the next scheduled backup
- `last_uploaded`: ISO timestamp of the last upload to Google Drive
- `backups_in_google_drive`: Number of backups in Google Drive
- `backups_in_home_assistant`: Number of backups in Home Assistant
- `size_in_google_drive`: Total size of backups in Google Drive
- `size_in_home_assistant`: Total size of backups in Home Assistant
- `free_space_in_google_drive`: Free space available in Google Drive
- `backups`: List of backup details (name, date, state, size, slug)

### Snapshot State Sensor (Legacy)

**Entity ID:** `sensor.snapshot_state`

Similar to Backup State Sensor but uses legacy naming (snapshots instead of backups).

### Backup Stale Binary Sensor

**Entity ID:** `binary_sensor.backup_stale`

**States:**
- `on`: Backups are stale (problem detected)
- `off`: Backups are current
- `unavailable`: Cannot connect to addon

## WebSocket Protocol

The integration connects to `ws://localhost:8099/ws` and receives JSON messages:

### Backup State Update
```json
{
  "type": "backup_state",
  "state": "backed_up",
  "attributes": {
    "last_backup": "2026-01-13T10:00:00",
    "backups_in_google_drive": 5,
    ...
  }
}
```

### Backup Stale Update
```json
{
  "type": "backup_stale",
  "is_stale": false
}
```

## Compatibility

- Requires Home Assistant 2023.1 or later
- Works with Google Drive Backup addon version X.X.X or later
- The addon includes fallback REST API support if integration is not installed

## Troubleshooting

### Sensors showing as unavailable

This is **expected behavior** when:
- The addon is not running
- Home Assistant is starting up (temporary)
- The addon is restarting

The sensors will automatically become available once the WebSocket connection is established.

### Integration not connecting

1. Check that the addon is running
2. Verify port 8099 is not blocked or in use by another service
3. Check Home Assistant logs: `Configuration` → `Logs` or search for `google_drive_backup`
4. Check addon logs for WebSocket server messages

### How to verify WebSocket is working

1. Check integration logs for "Connected to Google Drive Backup addon"
2. Check addon logs for "Integration client connected"
3. Visit addon's health endpoint: `http://localhost:8099/health` (from within HA)
4. Check sensor state - should not be "unavailable" when addon is running

### Manual debugging

Check WebSocket server health:
```bash
curl http://localhost:8099/health
```

Expected response:
```json
{"status": "ok", "clients": 1}
```

## Development

To modify the integration:

1. Make changes to files in `custom_components/google_drive_backup/`
2. Restart Home Assistant to load changes
3. Monitor logs for errors or connection issues

Key files:
- `__init__.py`: Integration setup and lifecycle
- `coordinator.py`: WebSocket client and connection management
- `sensor.py`: Backup and snapshot state sensors
- `binary_sensor.py`: Stale backup indicator

## Support

For issues or questions:
- GitHub Issues: https://github.com/jhenkens/hassio-google-drive-backup/issues
- Home Assistant Community: https://community.home-assistant.io/

## License

This integration is part of the Google Drive Backup addon project and follows the same license.
