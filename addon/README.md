# Kodi Home add-on

This is the first source scaffold for the local playback engine and Watchlist data.

- The service starts with Kodi.
- Playback tracking begins from Kodi's confirmed AV-start callback.
- A movie is removed from Watchlist after confirmed AV start.
- A show is removed after an episode starts, using Kodi's parent TV-show database ID. If a stable match is unavailable, the show remains listed.
- A selected item or failed launch does not remove it from Watchlist.
- Playback progress is saved locally every 30 seconds and when Kodi reports pause, seek, or stop.
- A natural playback end is recorded in local history. A deliberate stop only saves progress.
- The local Watchlist data supports add, explicit remove, and Released / Unreleased / All queries. Entries without a release date stay in Unreleased until metadata is refreshed.
- The database is stored in Kodi's per-add-on profile.

This is source code only. It has not been packaged or verified on the NVIDIA Shield. The Watchlist screens and user controls, Continue Watching presentation/resume controls, Up Next, and app groups are not implemented yet.
