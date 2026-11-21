# Kodi Home architecture

## Components

### Skin layer (skin/)

The Arctic Fuse 3 integration presents the Apps and Library hubs and the media information panel. The Shield baseline is Arctic Fuse 3.4.18. Keep skin changes isolated and traceable.

### Kodi Home add-on (addon/)

The Kodi Home video add-on provides independent Apps, Kodi Favourites, Umbrella Networks, library, and Watchlist routes. Watchlist membership changes only through explicit add/remove actions. The startup service refreshes cached artwork for the Apps hub and does not observe playback.

Continue Watching, Up Next, History, and automatic playback tracking have been removed from the active add-on interface and service. Their old SQLite tables remain untouched during upgrade so saved data is not deleted.

### Build and release tools (tools/)

Build from checked-in source and verify package contents and version metadata before release. Do not construct a new package by overlaying a few files onto an old Unified Lists ZIP.

## Data ownership

- **App groups:** local app identifiers, labels, group membership, sort order, selected logo, and selected background source.
- **Watchlist:** item identity, add date, release metadata, and the user's selected metadata/artwork values or source references.
- **Kodi library:** Kodi remains authoritative for library entries and .strm paths.
- **Legacy playback tables:** retained but no longer read or updated by Kodi Home.

## Manual Watchlist flow

1. The user selects an explicit Add to Watchlist action for a movie or TV show.
2. Kodi Home stores the item locally and refreshes available library metadata when the Watchlist is opened.
3. The user explicitly removes the item when desired.
4. Playing an item, selecting it, or opening its information page never changes Watchlist membership.

## Metadata and artwork

Metadata and fanart may come from available sources. Normalize them into Kodi list-item properties and use clear fallbacks so missing ratings, certificates, genres, logos, or fanart do not break the layout. IMDb and Rotten Tomatoes scores remain associated with their logos in the information panel.

## Visual behavior

- **Apps:** grey app tiles with white logos; the selected tile changes the hub background to app-specific artwork. Support either a moving branded background or a rotating pool of matching shows and films.
- **Library:** large, easy-to-read widgets with changing fanart and clear separation between library areas. Apply the same visual treatment to Umbrella .strm entries when artwork is available.
