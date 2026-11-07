# Kodi Home

A clean rebuild of the Kodi home experience for NVIDIA Shield and Kodi Omega.

## Project status

The add-on source stores local Continue Watching, Up Next, History, and Watchlist data, and now includes an NVIDIA Shield Apps hub with installed-app discovery, editable groups, app launching, and per-app logo/fanart fields. An Arctic Fuse 3.4.18 overlay now includes the info-panel changes, grey app tiles with white logos or name fallbacks, selected-app fanart backgrounds, and optional rotating image folders. The Apps add-on can also choose matching fanart from Kodi library metadata. A GitHub Actions packaging workflow builds the separate skin package. Automatic online retrieval of branded artwork and video splash clips still need implementing. The add-on and skin have not been installed or verified on the Shield.


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
