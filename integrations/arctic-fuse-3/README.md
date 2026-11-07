# Arctic Fuse 3 integration files

`homewidgets.json` contains Kodi Home's six local list sources in the same label/icon/path/target format used by the inspected Arctic Fuse 3 Skin Shortcuts widget preset.

## What it provides

- Continue Watching
- Up Next
- History
- Watchlist: All, Released, and Unreleased

Each source uses Kodi Home's plugin URL and returns Kodi video-library items with their available artwork.

## Important setup note

This JSON file is a source preset for maintainers to merge into Arctic Fuse's `skinvariables-shortcut-homewidgets.json`. Kodi and Arctic Fuse do not automatically load a JSON file from this Kodi Home repository, so adding this file alone does not change the Shield's home screen. The skin's exact installed version still needs to be checked before creating or installing a skin package; the reported Shield version and connected skin source version do not currently match.

For the source URLs and current compatibility note, see [the widget path reference](../../docs/arctic-fuse-widgets.md).
