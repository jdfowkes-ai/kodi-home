# Arctic Fuse 3.4.18 overlay

These files are a focused overlay for the upstream Arctic Fuse 3.4.18 source. They are not a complete skin package.

## Changes in this overlay

- Adds the genre to the video information line.
- Uses UK certificate badges for recognized UK MPAA values, retaining the text fallback for other ratings.
- Migrates the previous Trakt and Metacritic defaults to IMDb and Rotten Tomatoes Critic for Movies and TV Shows.
- Styles Kodi Home app tiles in square views with a slightly transparent mid-grey background, a centred clear logo, and a white app-name fallback.

The existing info panel places metadata after the synopsis. Its native TMDb Helper properties provide the rating values and artwork; Kodi Home playback tracking does not depend on TMDb Helper.

The GitHub Actions workflow checks out a pinned upstream source commit, applies this overlay and the included badge assets, changes the add-on ID to `skin.arctic.fuse.3.kodihome`, and packages a separate installable skin. The stock `skin.arctic.fuse.3` remains untouched. White clear-logo artwork can be supplied per app; without it, the tile displays the app name in white. Device installation and visual verification are still outstanding.

Source baseline: [jurialmunkey/skin.arctic.fuse.3, omega](https://github.com/jurialmunkey/skin.arctic.fuse.3/tree/omega). Upstream skin source is licensed CC BY-NC-SA 4.0. Preserve upstream attribution and license when distributing a derived skin.
