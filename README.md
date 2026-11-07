# Kodi Home

A clean rebuild of the Kodi home experience for NVIDIA Shield and Kodi Omega.

## Project status

The add-on source now stores local playback progress, Watchlist data, and completed History. It includes queries for Continue Watching, History, and Up Next; hides removed Continue Watching entries without discarding their resume point; and selects the next unwatched library episode after natural completion. A basic Kodi video add-on browser now exposes the four lists, list removal actions, and adding library movies or shows to Watchlist. A custom Arctic Fuse skin integration is not built yet.

The source has not been installed or verified on the Shield. No installable add-on or skin package has been built or deployed.

Your Shield baseline is Arctic Fuse 3.4.18. I checked the upstream `jurialmunkey/skin.arctic.fuse.3` omega source and its addon.xml declares 3.4.18, matching your Shield. The connected `jdfowkes-ai` fork's omega branch declares 3.4.48, so use the upstream 3.4.18 source as the skin baseline. Kodi Home has not modified or packaged skin XML yet. See docs/arctic-fuse-widgets.md.

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
