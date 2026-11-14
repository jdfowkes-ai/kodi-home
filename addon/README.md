# Kodi Home add-on

This is the source for the local playback engine, personal lists, and NVIDIA Shield Apps hub.

- The service starts with Kodi and tracks video through Kodi's player callbacks.
- A movie is removed from Watchlist after confirmed AV start.
- A show is removed after an episode starts, using Kodi's parent TV-show database ID. If a stable match is unavailable, the show remains listed.
- A selected item or failed launch does not remove it from Watchlist.
- Playback progress is saved locally every 30 seconds and when Kodi reports pause, seek, or stop.
- The Continue Watching query returns unfinished saved progress. Removing a row hides it while retaining its resume point; starting it again restores it to the list.
- A natural playback end is recorded in local History. History can be queried and entries removed.
- After a TV episode ends naturally, the service resolves the show's Kodi library ID from the episode tag or show title, then asks Kodi's video library for the next unwatched episode. That episode is stored in local Up Next and removed from Up Next when it starts.
- Watchlist storage supports add/update, explicit removal, and Released / Unreleased / All queries. Opening a Watchlist folder refreshes title, year, release date, and artwork from each linked Kodi library entry so newly available library metadata updates its folder automatically. Entries without a release date stay in Unreleased until metadata is available.
- The database is stored in Kodi's per-add-on profile.

Apps source supports installed-app discovery, editable groups, app launch, custom logos and backgrounds, rotating image folders, explicitly selected app fanart, and configurable live content feeds. App feeds can be selected from Umbrella's network catalogue, and the Home feed proxy removes Next Page controls. The app spotlight uses only an explicitly chosen feed and app artwork; it no longer falls back to matching library artwork. The feed can be set to an Umbrella network from the app tile context menu. Kodi Home includes a YouTube public Trending preset and a BBC iPlayer Most Popular preset when the Kodi iPlayer WWW add-on is installed.

GitHub Actions can package the add-on. Feed rendering and Home row spacing still need verification on the NVIDIA Shield.
