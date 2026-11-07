# Product requirements

This document records the new Kodi Home direction. It supersedes the Unified Lists project scope.

## 1. Information panel

- Show genres.
- Show the UK certification icon.
- Show IMDb and Rotten Tomatoes logos and their scores below the synopsis.
- Use metadata and artwork from available sources, with fallbacks when a source has no value.

## 2. Streams and widgets

- Umbrella handles stream resolution and stream widgets.
- The custom local playback tracker and personal lists must not rely on Umbrella, TMDb Helper, or Trakt.
- Kodi's own library remains in use and will contain Umbrella `.strm` entries.

## 3. Apps hub

- Manage NVIDIA Shield apps: add, remove, and group them.
- Support user-defined groups such as Favourites, Kids, Home Apps, Gaming, and Music.
- A group can appear as a hub widget.
- App tiles use a grey background with a white app logo.
- Moving through app tiles changes the hub fanart to match the selected app.
- App backgrounds may use a moving splash page or rotating/random show and movie artwork associated with the selected brand.

## 4. Local playback and personal lists

All four areas are local and accessible from the Kodi Home video add-on. Playback automatically adds items to Continue Watching, History, or Up Next as appropriate; users can remove entries from each list. Movies and shows from Kodi's library can be added to Watchlist from the add-on.

### Continue Watching

- Show movies and episodes with saved unfinished playback.
- Resume each item from its last saved playback position.
- Removing an item hides it from the list but preserves its resume point. Starting it again makes it visible.

### Up Next

- After an episode finishes naturally, show the next unwatched episode available in that show's Kodi library.
- Remove that episode from Up Next once playback starts.
- If Kodi has no next eligible episode for the show, show no Up Next entry for it.

### History

- Record watched movies and episodes when playback ends naturally.
- Allow entries to be removed.

### Watchlist

- Add and remove movies and shows for later.
- Refresh release metadata and sort the list into **Released**, **Unreleased**, and **All**.
- Remove a movie from Watchlist only after Kodi confirms that its audio or video has started.
- Remove a show after an episode of that show has actually started. Match the episode to its parent show by a stable Kodi show ID or another exact stable identifier; never guess by a similar title.
- Selecting an item, opening its information page, or failing before playback starts must leave it in Watchlist.

## 5. Kodi library presentation

- Continue using Kodi's library for Umbrella `.strm` entries.
- Give library widgets and fanart a prominent, visually distinctive presentation.
- Apply available metadata and artwork to `.strm` items as well as other library items.
