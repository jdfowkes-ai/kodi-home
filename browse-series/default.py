"""Browse series using Umbrella's own local watch progress."""
import sys

import xbmc
import xbmcgui
import xbmcplugin


UMBRELLA_PROGRESS = "plugin://plugin.video.umbrella/?action=local_shows_progress"


def main():
    handle = int(sys.argv[1])
    if not xbmc.getCondVisibility("System.HasAddon(plugin.video.umbrella)"):
        xbmcgui.Dialog().ok(
            "Browse Series",
            "Install and enable the Umbrella video add-on to browse your local series history.",
        )
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return

    item = xbmcgui.ListItem(label="Last Series Played")
    item.setInfo("video", {
        "title": "Last Series Played",
        "plot": "Open Umbrella's local TV series history, sorted by the last played episode.",
    })
    item.setArt({"icon": "DefaultFolder.png", "thumb": "DefaultFolder.png"})
    xbmcplugin.addDirectoryItem(
        handle=handle,
        url=UMBRELLA_PROGRESS,
        listitem=item,
        isFolder=True,
    )
    xbmcplugin.setContent(handle, "tvshows")
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)


if __name__ == "__main__":
    main()
