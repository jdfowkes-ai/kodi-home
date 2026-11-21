# Kodi Home add-on

Kodi Home provides a manually managed Watchlist and an NVIDIA Shield Apps hub.

- Watchlist entries are added and removed only through explicit user actions. Playback never removes an entry.
- Watchlist views include All, Released, and Unreleased. Opening the Watchlist refreshes available metadata from linked Kodi library items.
- Kodi Favourites and Umbrella Networks have independent plugin routes.
- The Apps hub supports installed-app discovery, editable groups, app launch, custom logos and backgrounds, rotating image folders, explicitly selected app fanart, and configurable live content feeds.
- The background service only refreshes the Apps hub's cached library artwork. It does not monitor playback.
- The add-on's prior Continue Watching, Up Next, and History screens and playback tracking have been removed. Their old database tables are left in place to avoid deleting saved data during upgrade, but the add-on no longer reads or updates them.

GitHub Actions packages the add-on and publishes the Kodi repository. The latest changes require verification on the NVIDIA Shield.
