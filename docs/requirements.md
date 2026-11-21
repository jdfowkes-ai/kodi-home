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

## 4. Watchlist

- Manage the Watchlist manually: users explicitly add or remove movies and TV shows.
- Playback, selecting an item, and opening its information page do not change Watchlist membership.
- Refresh available release metadata and sort the list into **Released**, **Unreleased**, and **All**.
- Keep Continue Watching, Up Next, and History playback tracking out of Kodi Home.

## 5. Kodi library presentation

- Continue using Kodi's library for Umbrella `.strm` entries.
- Give library widgets and fanart a prominent, visually distinctive presentation.
- Apply available metadata and artwork to `.strm` items as well as other library items.
