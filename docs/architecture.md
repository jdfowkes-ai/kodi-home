# Initial architecture

## Components

### Skin layer (`skin/`)

Build a focused Arctic Fuse 3 based interface for the Apps and Library hubs and the media information panel. The user confirmed the Shield baseline is Arctic Fuse 3.4.18, and the upstream `jurialmunkey/skin.arctic.fuse.3` omega branch currently declares 3.4.18. Use that source as the implementation baseline; the connected `jdfowkes-ai` fork's omega branch declares 3.4.48. Keep custom changes isolated and traceable instead of carrying forward the broken experimental branches.

### Kodi Home add-on (`addon/`)

Own the app catalogue and groups, local lists, and playback tracking. Store user data in Kodi's add-on profile using a small local database. A Kodi video add-on plugin exposes the local lists, Movie and TV Show library widgets, and library-based Watchlist controls through Kodi's standard list interface. Use Kodi playback callbacks to record starts, progress, completion, and stops for library items, including `.strm` files.

### Build and release tools (`tools/`)

Build from checked-in source and verify package contents and version metadata before any release. Do not construct a new package by overlaying a few files onto an old Unified Lists ZIP.

## Data ownership

- **App groups:** local app identifiers, labels, group membership, sort order, selected logo, and selected background source.
- **Playback state:** stable Kodi library identity, media type, playback position, duration, completion state, and update time.
- **History:** watched item identity and watched timestamps.
- **Watchlist:** item identity, add date, release metadata, and the user's selected metadata/artwork values or source references.
- **Kodi library:** Kodi remains authoritative for library entries and `.strm` paths; the custom add-on keeps its own playback and personal-list state.

## Playback flow

1. The user selects a Kodi library item.
2. Kodi plays the library item's file or `.strm` target. Umbrella may resolve the stream behind a `.strm` entry.
3. Kodi Home observes Kodi's player events and records progress locally without calling Umbrella, TMDb Helper, or Trakt for tracking.
4. If that item is in Watchlist, Kodi Home removes a movie after confirmed AV start. For a show, it removes the matching show entry only after one of its episodes starts and Kodi supplies the parent show ID. A selection or failed launch leaves the entry untouched.
5. Continue Watching reads unfinished saved progress. Removing a row hides it while preserving the resume point; starting the item again restores it. Natural completion records History and selects the next unwatched episode available in Kodi's library for Up Next. When that episode starts, its Up Next row is consumed.

## Local playback and personal-list source slices

The add-on source uses Kodi's startup service extension and an `xbmc.Player` callback monitor:

- `onAVStarted` begins tracking after Kodi reports an active audio/video stream.
- The same confirmed-start callback triggers Watchlist removal. Movie entries match by stable item key or Kodi movie database ID; show entries match by parent TV-show database ID. It does not fuzzy-match titles.
- Watchlist storage supports adding/updating an item, explicit removal, and Released / Unreleased / All queries. Missing release dates remain in Unreleased until metadata is supplied.
- Position is saved locally at 30-second intervals and on pause, seek, or deliberate stop.
- A deliberate stop saves progress without marking the item watched.
- Kodi's natural playback-ended callback marks an item complete and records a History row.
- Local queries expose Continue Watching, History, and Up Next. Continue Watching removal hides a row without deleting its progress; History and Up Next entries can be removed.
- When an episode ends, the service calls Kodi's `VideoLibrary.GetEpisodes` JSON-RPC method for the parent show, chooses the next unwatched episode after the completed season/episode, and stores its library ID and file path in Up Next. Starting that exact episode removes it from Up Next.
- The SQLite database is placed in the add-on profile.

This describes source behavior only. It has not been installed or verified on the Shield. The add-on now includes a basic Kodi list browser and context actions. A custom Arctic Fuse visual layer, remote-focus design, resume controls polish, and Apps management are still pending. Kodi documents `onAVStarted` for confirmed playback, `getPlayingItem()` for the current item, and `getTime()` / `getTotalTime()` for playback position and duration. Kodi's `VideoPlayer.TvShowDBID` infolabel provides the current episode's parent show database ID. Kodi's `VideoLibrary.GetEpisodes` method supports filtering the episode list by a TV-show database ID and requesting episode properties. Kodi plugin sources can populate standard directory views with `xbmcplugin.addDirectoryItem` and resolve playback with `setResolvedUrl`; the player API exposes `play()` for context actions. See the [Kodi JSON-RPC VideoLibrary API](https://kodi.wiki/view/JSON-RPC_API/v12#VideoLibrary.GetEpisodes), [plugin source guide](https://kodi.wiki/view/Plugin_sources), and [Kodi Python plugin API](https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmcplugin.html). See the [Kodi Player API](https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python___player.html), [player callbacks](https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python___player_c_b.html), [Kodi info labels](https://kodi.wiki/view/InfoLabels), and [service add-on guide](https://kodi.wiki/view/Service_add-ons).

## Metadata and artwork

Metadata and fanart may come from any available source. Normalize them into Kodi list-item properties and use a clear fallback order so a missing rating, certificate, genre, logo, or fanart image does not break the layout. The IMDb and Rotten Tomatoes scores must remain associated with their logos in the information panel.

## Visual behavior

- **Apps:** grey app tiles with white logos; the selected tile changes the hub background to app-specific artwork. Support either a moving branded background or a rotating pool of matching shows and films.
- **Library:** large, easy-to-read widgets with changing fanart and clear separation between library areas. Apply the same visual treatment to Umbrella `.strm` entries when artwork is available.

## Decisions to verify before implementation

- Completion threshold and the user-facing resume behavior.
- Whether the selected Kodi library ordering should account for special episode sort metadata on Shield.
- Which animated app backgrounds are available locally or from chosen sources, and how they should fall back on Shield.
- How often release metadata and artwork refresh, and how to handle unavailable metadata.
- Kodi and Arctic Fuse 3 compatibility details on the actual Shield installation.
