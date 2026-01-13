# Google Drive Backup Integration Setup Guide

This guide explains how to set up the Home Assistant custom integration that pairs with the Google Drive Backup addon using WebSocket-based local push updates.

## Overview

The integration and addon work together using a WebSocket connection:
- **Addon**: Runs a WebSocket server on port 8099
- **Integration**: Connects as a WebSocket client to receive real-time updates
- **Benefits**: Zero polling, proper availability tracking, and better performance

## Quick Start

1. **Install the Integration**
   ```bash
   cd /config
   mkdir -p custom_components
   cp -r /path/to/custom_components/google_drive_backup custom_components/
   ```

2. **Restart Home Assistant**
   - Navigate to `Settings` → `System` → `Restart`
   - Or use CLI: `ha core restart`

3. **Verify Connection**
   - Check that sensors appear: `sensor.backup_state`, `sensor.snapshot_state`, `binary_sensor.backup_stale`
   - Sensors should show real data (not "unavailable") when addon is running
   - Check logs for "Connected to Google Drive Backup addon"

## Installation Methods

### Method 1: Manual Installation (Recommended)

1. Download or copy the integration files
2. Place in your Home Assistant config directory:
   ```
   config/
   └── custom_components/
       └── google_drive_backup/
           ├── __init__.py
           ├── manifest.json
           ├── coordinator.py
           ├── sensor.py
           ├── binary_sensor.py
           └── README.md
   ```

3. Restart Home Assistant

### Method 2: Git Clone (For Development)

```bash
cd /config/custom_components
git clone https://github.com/jhenkens/hassio-google-drive-backup.git temp
mv temp/custom_components/google_drive_backup ./
rm -rf temp
```

### Method 3: HACS (Future)

When available through HACS:
1. Open HACS in Home Assistant
2. Search for "Google Drive Backup"
3. Click Install
4. Restart Home Assistant

## Verification

### Check Integration is Loaded

1. **Via Logs**:
   - Go to `Settings` → `System` → `Logs`
   - Search for `google_drive_backup`
   - Look for: "Google Drive Backup coordinator started"

2. **Via Developer Tools**:
   - Go to `Developer Tools` → `States`
   - Search for entities starting with `sensor.backup` or `binary_sensor.backup_stale`

3. **Via WebSocket Health Check** (from Home Assistant host):
   ```bash
   curl http://localhost:8099/health
   ```
   Expected output:
   ```json
   {"status": "ok", "clients": 1}
   ```

### Verify Sensors are Working

Check each sensor's state:

**Backup State Sensor:**
```yaml
entity_id: sensor.backup_state
state: backed_up  # or waiting, error
attributes:
  last_backup: "2026-01-13T10:00:00"
  backups_in_google_drive: 5
  backups_in_home_assistant: 3
  # ... more attributes
```

**Binary Sensor:**
```yaml
entity_id: binary_sensor.backup_stale
state: off  # or on if backups are stale
```

## Configuration

### No Configuration Needed!

The integration uses sensible defaults:
- **Host**: `localhost` (addon runs on same system)
- **Port**: `8099` (default WebSocket port)
- **Auto-reconnect**: Enabled with 5-second retry interval
- **Heartbeat**: 30-second ping/pong

### Advanced: Custom Configuration (If Needed)

If you need to customize the connection (rare), you can modify the integration code:

Edit `custom_components/google_drive_backup/__init__.py`:
```python
# Change these constants
DEFAULT_HOST = "localhost"  # Change if addon is remote
DEFAULT_PORT = 8099         # Change if port conflicts
```

## Addon Setup

The addon automatically starts the WebSocket server when it launches. No configuration needed!

### Verify Addon WebSocket Server

Check addon logs for:
```
Integration WebSocket server started on port 8099
```

When integration connects, you'll see:
```
Integration client connected (id: 12345). Total clients: 1
```

## Troubleshooting

### Sensors Show "Unavailable"

**This is expected** when:
- Addon is not running
- Home Assistant is starting (temporary)
- Connection is temporarily lost

**To fix persistent unavailability:**
1. Check addon is running: `Settings` → `Add-ons` → `Google Drive Backup`
2. Check addon logs for errors
3. Restart addon if needed
4. Check integration logs for connection errors

### Integration Not Connecting

**Check Port 8099:**
```bash
# From Home Assistant host
netstat -tlnp | grep 8099
# Should show the addon listening
```

**Check Firewall:**
- Port 8099 should be accessible on localhost
- If using Docker, ensure port is exposed (usually automatic)

**Check Integration Logs:**
```
Settings → System → Logs
Search: "google_drive_backup"
```

Look for errors like:
- "Connection error: ..."
- "Connection timeout"

### WebSocket Connection Drops Frequently

**Possible causes:**
1. Addon crashes or restarts frequently (check addon logs)
2. Network issues (rare on localhost)
3. Resource constraints (CPU/memory)

**Solutions:**
- Check Home Assistant system resources
- Review addon logs for crashes
- Increase addon memory allocation if needed

### Sensors Not Updating

**Verify WebSocket is connected:**
1. Check integration logs for "Connected to Google Drive Backup addon"
2. Check addon logs for "Integration client connected"
3. Test health endpoint: `curl http://localhost:8099/health`

**If connected but not updating:**
1. Check addon is performing backups (check addon UI)
2. Verify backup updates are enabled in addon settings
3. Check for errors in haupdater logs

## Using the Sensors

### Automation Example: Notify on Stale Backups

```yaml
automation:
  - alias: "Alert: Backups are Stale"
    trigger:
      - platform: state
        entity_id: binary_sensor.backup_stale
        to: "on"
        for:
          minutes: 10
    action:
      - service: notify.notify
        data:
          title: "⚠️ Backup Problem"
          message: "Backups are stale! Check the addon status."
```

### Lovelace Card Example

```yaml
type: entities
title: Google Drive Backup
entities:
  - entity: sensor.backup_state
    name: Status
  - entity: binary_sensor.backup_stale
    name: Backups Stale
  - type: attribute
    entity: sensor.backup_state
    attribute: last_backup
    name: Last Backup
  - type: attribute
    entity: sensor.backup_state
    attribute: backups_in_google_drive
    name: Backups in Drive
  - type: attribute
    entity: sensor.backup_state
    attribute: backups_in_home_assistant
    name: Backups in HA
```

## Uninstallation

To remove the integration:

1. Stop Home Assistant
2. Remove the integration directory:
   ```bash
   rm -rf /config/custom_components/google_drive_backup
   ```
3. Start Home Assistant

The addon will continue to work normally and fall back to REST API for sensor updates.

## Migration from Old Version

If you're upgrading from a service-based integration to this WebSocket version:

1. **Backup your configuration** (just in case)
2. **Replace the integration files** with the new WebSocket version
3. **Restart Home Assistant**
4. **Verify sensors are working** (check they're not unavailable)

No configuration changes needed - the upgrade is seamless!

## FAQ

**Q: Do I need to configure anything?**
A: No! It auto-discovers and connects to the addon automatically.

**Q: What happens if the addon restarts?**
A: The integration automatically reconnects within 5 seconds. Sensors will briefly show "unavailable" then recover.

**Q: Can I use this without the addon?**
A: No, this integration is specifically designed to work with the Google Drive Backup addon.

**Q: Does this work with Home Assistant OS, Supervised, Container, and Core?**
A: Yes! It works with all Home Assistant installation types.

**Q: Will old automations break?**
A: No, the sensor names and attributes remain the same.

**Q: Why WebSocket instead of REST API?**
A: WebSocket provides real-time push updates, proper availability tracking, and better performance with zero polling overhead.

## Support

- **GitHub Issues**: https://github.com/jhenkens/hassio-google-drive-backup/issues
- **Community Forum**: https://community.home-assistant.io/
- **Addon Documentation**: See addon README

## Advanced Topics

### Monitoring Connection Health

Create a sensor to track connection status:

```yaml
template:
  - binary_sensor:
      - name: "Backup Integration Connected"
        state: "{{ not is_state('sensor.backup_state', 'unavailable') }}"
        device_class: connectivity
```

### Multiple Addon Instances

If you run multiple Google Drive Backup addons (advanced setup):
1. Each addon needs a different WebSocket port
2. You'll need to configure the integration for each instance
3. Create multiple integration instances (requires config flow support)

This is an advanced scenario not covered by the default setup.
