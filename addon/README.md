# Kodi Home add-on

This is the source for the local playback engine, personal lists, and NVIDIA Shield Apps hub.

- The service starts with Kodi and tracks video through Kodi's player callbacks.
- A movie is removed from Watchlist after confirmed AV start.
- A show is removed after an episode starts, using Kodi's parent TV-show database ID. If a stable match is unavailable, the show remains listed.
- A selected item or failed launch does not remove it from Watchlist.
- Playback progress is saved locally every 30 seconds and when Kodi reports pause, seek, or stop.
- The Continue Watching query returns unfinished saved progress. Removing a row hides it while retaining its resume point; starting it again restores it to the list.
- A natural playback end is recorded in local History. History can be queried and entries removed.
- After a TV episode ends naturally, the service asks Kodi's video library for the next unwatched episode in the same show. That episode is stored in local Up Next and removed from Up Next when it starts.
- Watchlist storage supports add/update, explicit removal, and Released / Unreleased / All queries. Opening a Watchlist folder refreshes title, year, release date, and artwork from each linked Kodi library entry so newly available library metadata updates its folder automatically. Entries without a release date stay in Unreleased until metadata is available.
- The database is stored in Kodi's per-add-on profile.

Apps source supports installed-app discovery, editable groups, app launch, custom logos and backgrounds, rotating image folders, and library-matched fanart fallback. Version 0.4.9 replaces the removed `xbmc.translatePath` call with `xbmcvfs.translatePath` when preparing app-group fanart folders, for Kodi 21 compatibility.

GitHub Actions can package the add-on, but Kodi Home 0.4.9 has not yet been tested on the NVIDIA Shield.
