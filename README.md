# Kodi Home

A clean rebuild of the Kodi home experience for NVIDIA Shield and Kodi Omega.

## Project status

The first local playback service source scaffold is in `addon/`. It stores playback progress and completed history in a local SQLite database. It has not been installed or verified on the Shield.

No installable add-on or skin package has been built or deployed.

The current user-reported stable skin baseline is Arctic Fuse 3 version 3.4.18. Confirm the version on the Shield before preparing a device package.

## Product boundaries

- Umbrella remains responsible for stream resolution and its stream widgets.
- Kodi's video library remains enabled for Umbrella `.strm` entries.
- Kodi Home owns local playback progress, Continue Watching, Up Next, History, and Watchlist data.
- The Kodi Home playback tracker must not depend on Umbrella APIs, TMDb Helper, or Trakt. It observes Kodi playback of library items, including `.strm` items.
- Metadata and artwork may be collected from any available sources.

## Main areas

- **Information panel:** genres and the UK certificate icon; IMDb and Rotten Tomatoes logos and scores below the synopsis.
- **Apps hub:** user-managed Shield apps and groups, branded app tiles, and app-specific changing fanart or moving artwork.
- **Library hub:** prominent library widgets and fanart for Kodi library entries, including Umbrella `.strm` items.
- **Local playback:** resume progress, next episodes, watched history, and editable watchlists with Released, Unreleased, and All views.

See [requirements](docs/requirements.md), [architecture](docs/architecture.md), and the [add-on source](addon/README.md).
