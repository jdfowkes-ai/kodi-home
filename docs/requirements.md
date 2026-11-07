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

All four areas are locally managed and allow entries to be added and removed.

### Continue Watching

- Show movies and episodes that are partway through.
- Resume each item from its last saved playback position.

### Up Next

- After an episode is finished, show the next episode in that series.

### History

- Record watched movies and shows.

### Watchlist

- Add and remove movies and shows for later.
- Refresh release metadata and sort the list into **Released**, **Unreleased**, and **All**.

## 5. Kodi library presentation

- Continue using Kodi's library for Umbrella `.strm` entries.
- Give library widgets and fanart a prominent, visually distinctive presentation.
- Apply available metadata and artwork to `.strm` items as well as other library items.
