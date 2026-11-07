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

## Skin source version note

You confirmed the Shield baseline is **Arctic Fuse 3.4.18**. I checked the upstream [Arctic Fuse 3 addon.xml](https://github.com/jurialmunkey/skin.arctic.fuse.3/blob/omega/addon.xml); its omega branch declares **3.4.18**, matching your Shield. The connected [jdfowkes-ai fork](https://github.com/jdfowkes-ai/skin.arctic.fuse.3/blob/omega/addon.xml) declares **3.4.48**. Use the upstream 3.4.18 source as the baseline for any skin-specific changes. The widget sources remain version-neutral.
