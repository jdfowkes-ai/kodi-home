# Arctic Fuse 3 widget paths

Kodi Home exposes stable plugin paths that Arctic Fuse 3 can use for home menu items and widgets. These paths use Kodi's standard add-on browser and do not require changing Arctic Fuse XML.

## Home menu shortcut

Use the Kodi Home video add-on root:

plugin://plugin.video.kodihome/

## List widget paths

| Widget | Path |
| --- | --- |
| Continue Watching | plugin://plugin.video.kodihome/?action=list&name=continue |
| Up Next | plugin://plugin.video.kodihome/?action=list&name=up_next |
| History | plugin://plugin.video.kodihome/?action=list&name=history |
| Watchlist · All | plugin://plugin.video.kodihome/?action=watchlist_items&bucket=all |
| Watchlist · Released | plugin://plugin.video.kodihome/?action=watchlist_items&bucket=released |
| Watchlist · Unreleased | plugin://plugin.video.kodihome/?action=watchlist_items&bucket=unreleased |

Playback list entries retain available Kodi artwork such as poster, thumb, landscape, and fanart. Watchlist entries use artwork from their Kodi library metadata. Arctic Fuse can use these as the selected widget and focused-item background sources.

These are widget content endpoints. They do not install a preset home layout or change the skin's visual style.

## Library widget paths

| Widget | Path |
| --- | --- |
| Movies library | plugin://plugin.video.kodihome/?action=library_items&media_type=movie |
| TV Shows library | plugin://plugin.video.kodihome/?action=library_items&media_type=tvshow |

The library widgets request each Kodi item's poster, landscape, clear logo, and fanart as available, including artwork attached to Umbrella `.strm` entries. The skin overlay tags these entries and prioritizes their own fanart for the focused background, independently of TMDb Helper's blur properties. Choose a poster, landscape, or square view in Arctic Fuse to control the row's tile shape.

## Skin source version note

You confirmed the Shield baseline is **Arctic Fuse 3.4.18**. I checked the upstream [Arctic Fuse 3 addon.xml](https://github.com/jurialmunkey/skin.arctic.fuse.3/blob/omega/addon.xml); its omega branch declares **3.4.18**, matching your Shield. The connected [jdfowkes-ai fork](https://github.com/jdfowkes-ai/skin.arctic.fuse.3/blob/omega/addon.xml) declares **3.4.48**. Use the upstream 3.4.18 source as the baseline for any skin-specific changes. The widget sources remain version-neutral.

## Native update check — 7 November 2026

The upstream `jurialmunkey/skin.arctic.fuse.3` omega branch still declares version **3.4.18**, matching the Shield baseline. The branch has newer source commits, but no higher add-on version is declared there. The maintainer's Kodi repository identifies itself as an alpha repository. This checks public source only; the Shield's configured repositories and pending updates have not been inspected.

## Apps hub paths

- Apps groups: `plugin://plugin.video.kodihome/?action=apps`
- An app group as a widget, for example Home Apps: `plugin://plugin.video.kodihome/?action=app_group&group_name=Home+Apps`

See [the Apps hub notes](apps-hub.md) for app discovery, group management, launch behavior, and visual work still outstanding.


## Optional Kodi Home Library preset

The Kodi Home skin build adds **Kodi Home Library** to Arctic Fuse's Widget Sets chooser when the Kodi Home add-on is enabled. It adds a Movies Library widget and a TV Library widget that use Kodi Home's library browser, preserving the Kodi library artwork used for posters and focused fanart.

This is an explicit setup choice. Selecting it applies Arctic Fuse's Library preset to the wider hub shortcut setup; installing or updating the skin does not apply the preset automatically. You can continue configuring widgets and hubs in Arctic Fuse after applying it.
