# Initial architecture

## Components

### Skin layer (`skin/`)

Build a focused Arctic Fuse 3 based interface for the Apps and Library hubs and the media information panel. The currently reported Shield baseline is Arctic Fuse 3.4.18; verify it on the device before selecting source or packaging a change. Keep custom changes isolated and traceable instead of carrying forward the broken experimental branches.

### Kodi Home add-on (`addon/`)

Own the app catalogue and groups, local lists, and playback tracking. Store user data in Kodi's add-on profile using a small local database. Use Kodi playback callbacks to record starts, progress, completion, and stops for library items, including `.strm` files.

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
4. Continue Watching uses the locally saved position. Completion moves an item into History and makes the next available episode eligible for Up Next.

## Metadata and artwork

Metadata and fanart may come from any available source. Normalize them into Kodi list-item properties and use a clear fallback order so a missing rating, certificate, genre, logo, or fanart image does not break the layout. The IMDb and Rotten Tomatoes scores must remain associated with their logos in the information panel.

## Visual behavior

- **Apps:** grey app tiles with white logos; the selected tile changes the hub background to app-specific artwork. Support either a moving branded background or a rotating pool of matching shows and films.
- **Library:** large, easy-to-read widgets with changing fanart and clear separation between library areas. Apply the same visual treatment to Umbrella `.strm` entries when artwork is available.

## Decisions to verify before implementation

- What playback threshold marks an item complete, and how often progress is saved.
- How to choose the next episode when an episode is absent from the Kodi library.
- Which animated app backgrounds are available locally or from chosen sources, and how they should fall back on Shield.
- How often release metadata and artwork refresh, and how to handle unavailable metadata.
- Kodi and Arctic Fuse 3 compatibility details on the actual Shield installation.
