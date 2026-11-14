# Kodi Home

A clean rebuild of the Kodi home experience for NVIDIA Shield and Kodi Omega.

## Project status

The add-on stores local Continue Watching, Up Next, History, and Watchlist data, and includes an NVIDIA Shield Apps hub with installed-app discovery, editable groups, app launching, per-app artwork, and optional user-selected rotating image folders. Each app can choose a live feed from Umbrella's network catalogue. Home app feeds now filter out pagination buttons, and app heroes no longer inherit matching artwork from the Kodi library. The Arctic Fuse 3.4.18 overlay includes the info-panel changes and branded app tiles. GitHub Actions builds the add-on and skin packages separately. The latest add-on package is published through the Kodi repository; its behaviour still needs verification on the Shield.


Your Shield baseline is Arctic Fuse 3.4.18. The info-panel overlay and skin builder use the matching upstream 3.4.18 source and package as a separate add-on. The connected `jdfowkes-ai` fork declares 3.4.48. See [widget paths](docs/arctic-fuse-widgets.md) and [Apps hub details](docs/apps-hub.md).

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
