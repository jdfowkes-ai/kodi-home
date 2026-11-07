# Kodi Home add-on

This is the first source scaffold for the local playback engine.

- The service starts with Kodi.
- Playback tracking begins from Kodi's confirmed AV-start callback.
- Playback progress is saved locally every 30 seconds and when Kodi reports pause, seek, or stop.
- A natural playback end is recorded in local history. A deliberate stop only saves progress.
- The database is stored in Kodi's per-add-on profile.

This is source code only. It has not been packaged or verified on the NVIDIA Shield. Continue Watching presentation, resume controls, Up Next, user-managed Watchlist, and app groups are not implemented yet.
