# Kodi Home add-on

This is the source scaffold for the local playback engine and personal lists.

- The service starts with Kodi and tracks video through Kodi's player callbacks.
- A movie is removed from Watchlist after confirmed AV start.
- A show is removed after an episode starts, using Kodi's parent TV-show database ID. If a stable match is unavailable, the show remains listed.
- A selected item or failed launch does not remove it from Watchlist.
- Playback progress is saved locally every 30 seconds and when Kodi reports pause, seek, or stop.
- The Continue Watching query returns unfinished saved progress. Removing a row hides it while retaining its resume point; starting it again restores it to the list.
- A natural playback end is recorded in local History. History can be queried and entries removed.
- After a TV episode ends naturally, the service asks Kodi's video library for the next unwatched episode in the same show. That episode is stored in local Up Next and removed from Up Next when it starts.
- Watchlist storage supports add/update, explicit removal, and Released / Unreleased / All queries. Entries without a release date stay in Unreleased until metadata is refreshed.
- The database is stored in Kodi's per-add-on profile.

This is source code only. It has not been packaged or verified on the NVIDIA Shield. The screens, navigation, and controls for these lists, the resume prompt, and Apps management are not implemented yet.
