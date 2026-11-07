"""Kodi Home background service entry point."""

import xbmc
import xbmcaddon

from resources.lib.kodihome import KodiHomePlayer, LocalStore


ADDON = xbmcaddon.Addon()
LOG_PREFIX = "Kodi Home"


def main():
    monitor = xbmc.Monitor()
    try:
        store = LocalStore(ADDON)
        player = KodiHomePlayer(store)
    except Exception as exc:
        xbmc.log("%s: service could not start: %s" % (LOG_PREFIX, exc), xbmc.LOGERROR)
        return

    xbmc.log("%s: local playback service started" % LOG_PREFIX, xbmc.LOGINFO)
    try:
        while not monitor.abortRequested():
            player.tick()
            if monitor.waitForAbort(5):
                break
    finally:
        xbmc.log("%s: local playback service stopped" % LOG_PREFIX, xbmc.LOGINFO)


if __name__ == "__main__":
    main()
