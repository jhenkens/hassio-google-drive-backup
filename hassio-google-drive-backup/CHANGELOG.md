## v0.113.0 [2026-01-13]

- Added Home Assistant custom integration for local push updates via WebSocket
- WebSocket server republishes latest state to clients on connection/reconnection for immediate updates
- Fixed WebSocket server port conflict with ingress (moved from 8099 to 8100)
- Added integration_ws_port configuration setting
- Added enhanced connection logging for troubleshooting
- Added integration icons for better UI display
- Integration entities are now grouped under a device for better organization
- Integration entities are diagnostic sensors (hidden by default in UI)
- Added HACS support for easy integration installation
- Added UI-based installation via config flow
- Removed sensor enable/disable settings from addon configuration (now controlled by installing/uninstalling the integration)
- Fixed pip installation issues by using virtual environment for all Python packages
- Addon now builds locally on the machine instead of using prebuilt container images
- Removed all "snapshot" vs "backup" terminology options - addon now consistently uses "backup" terminology

## v0.112.1 [2023-11-03]

- Added warnings about using the "Stop Addons" feature.  I plan on removing this in the near future.  If you'd like to keep the feature around, please give your feedback in [this GitHub issue](https://github.com/sabeechen/hassio-google-drive-backup/issues/940).
- When backups are stuck in the "pending" state, the addon now provides you with the Supervisor logs to help figure out whats wrong.
- Added support for the "exclude Home Assistant database" options for automatic backups
- Added configuration options to limit the speed of uploads to Google Drive
- When Google Drive doesn't have enough space, the addon now explains how much space you're using and how much is left.  This was a source of confusion for users.
- When the addon halts because it needs to delete more than one backup, it now tells you which backups will be deleted.
- Fixed a bug when using "stop addons" that prevented it from recognizing addons in the "starting" state.
- The addon's containers are now donwloaded from Github (previously was DockerHub)
- Added another redundant token provider, hosted on heroku, that the addon uses for its cloud-required component when you aren't using your own google app credentials.

## v0.111.1 [2023-06-19]

- Support for the new network storage features in Home Assistant.  The addon will now create backups in what Home Assistant has configured as its default backup location.  This can be overridden in the addon's settings.
- Raised the addon's required permissions to "Admin" in order to access the supervisor's mount API.
- Fixed a CSS error causing toast messages to render partially off screen on small displays.
- Fixed misreporting of some error codes from Google Drive when a partial upload can't be resumed.

## v0.110.4 [2023-04-28]

- Fix a whitespace error causing authorization to fail.

## v0.110.3 [2023-03-24]

- Fix an error causing "Days Between Backups" to be ignored when "Time of Day" for a backup is set.
- Fix a bug causing some timezones to make the addon to fail to start.

## v0.110.2 [2023-03-24]

- Fix a potential cause of SSL errors when communicating with Google Drive
- Fix a bug causing backups to be requested indefinitely if scheduled during DST transitions.

## v0.110.1 [2023-01-09]

- Adds some additional options for donating
- Mitgigates SD card corruption by redundantly storing config files needed for addon startup.
- Avoid global throttling of Google Drive API calls by:
  - Making sync intervals more spread out and a little random.
  - Syncing more selectively when there are modifications to the /backup directory.
  - Caching data from Google Drive for short periods during periodic syncing.
  - Backing off for a longer time (2 hours) when the addon hits permanent errors.
- Fixes CSS issues that made the logs page hard to use.
