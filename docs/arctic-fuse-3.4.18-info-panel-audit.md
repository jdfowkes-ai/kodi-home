# Arctic Fuse 3.4.18 information panel audit

## Baseline

The user's Shield baseline is Arctic Fuse 3.4.18. The upstream `jurialmunkey/skin.arctic.fuse.3` `omega` branch currently declares 3.4.18 in `addon.xml`. This audit uses that source. The separate connected personal fork declares 3.4.48 and is not the implementation base.

## Relevant source files

- [`1080i/DialogVideoInfo.xml`](https://github.com/jurialmunkey/skin.arctic.fuse.3/blob/omega/1080i/DialogVideoInfo.xml) wires the video information dialog to `DialogInfo_Info_Group` and `DialogInfo_VideoDetails`.
- [`1080i/Includes_Info.xml`](https://github.com/jurialmunkey/skin.arctic.fuse.3/blob/omega/1080i/Includes_Info.xml) builds the information panel in this order: detail line, synopsis/plot, then metadata. That gives the required location for IMDb and Rotten Tomatoes logos and scores below the synopsis.
- [`shortcuts/skinvariables-startup.json`](https://github.com/jurialmunkey/skin.arctic.fuse.3/blob/omega/shortcuts/skinvariables-startup.json) supplies default rating slots.
- [`media/flags/color/ratings/`](https://github.com/jurialmunkey/skin.arctic.fuse.3/tree/omega/media/flags/color/ratings) contains rating logo assets.

## Gaps against the agreed design

- The metadata row supports IMDb, Rotten Tomatoes critic, and Rotten Tomatoes user ratings, but those entries are shown only when the matching Skin String slots are selected and TMDb Helper metadata is available.
- The startup defaults currently select Trakt and Metacritic for Movies and TV Shows. The custom setup needs IMDb and Rotten Tomatoes as its visible defaults.
- Genre is currently available as an optional plotline selection. It is not guaranteed to appear as its own fixed field in the information line.
- The information line displays the MPAA value as text. It does not provide the agreed UK certificate icon treatment in the upstream 3.4.18 source.
- The connected skin fork contains a separate UK certificate icon implementation and corresponding UK badge assets. These can be used as a reference, but should be ported and reviewed against the confirmed 3.4.18 upstream files rather than copied as a full fork.

## First skin patch status

The source overlay now adds genre as a persistent field, maps recognized UK MPAA values to UK certificate badge assets while retaining a text fallback, and migrates the previous Trakt/Metacritic defaults to IMDb/Rotten Tomatoes Critic. The build script refuses any source skin whose version is not 3.4.18 and packages the result under a separate Kodi Home skin add-on ID.

The GitHub Actions build workflow is in place. The package has not yet been confirmed as built or installed, and the visual result still needs Shield verification.
