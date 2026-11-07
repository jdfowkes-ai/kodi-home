# NVIDIA Shield Apps hub

Kodi Home now has a local app catalogue for the NVIDIA Shield.

## Groups

The first run creates these editable groups:

- Favourites
- Kids
- Home Apps
- Gaming
- Music

You can create, rename, and delete groups. Apps can belong to more than one group.

## Add and launch apps

Open the Kodi Home add-on and choose **Apps**. Choose **Add installed app** or open a group and choose **Add installed app**. Kodi Home reads the installed Android apps from Kodi's native `androidapp://sources/apps/` directory; selecting an app adds it to the chosen group.

Selecting an app from a group opens its native Android package through Kodi's `StartAndroidActivity` built-in. App membership and artwork are stored locally in Kodi Home's add-on profile.

## Artwork

Each app keeps its Android icon and can have a custom clear logo and fanart image selected from Kodi's configured file sources. Use the app context menu's **Choose rotating background folder** action to select a folder of brand-related images for that app. **Clear rotating background folder** returns it to the single fanart image. The Arctic Fuse overlay now styles only the square app tile with a slightly transparent mid-grey background and a centred clear logo. If no clear logo is set, it shows the app name in white. As focus moves across the widget row, Arctic Fuse now prioritizes the selected app item's own fanart for the background, ahead of TMDb Helper background properties. If a rotating folder is set, Arctic Fuse shuffles its images every eight seconds with a crossfade; otherwise it uses the single fanart image. Kodi skin textures support animated GIFs, so a folder can also include a compatible GIF.

The animated or rotating brand-related artwork remains pending. The tile overlay is source code only; installation and Shield verification have not happened yet.

## Paths

- Apps group list: `plugin://plugin.video.kodihome/?action=apps`
- A group as a widget, for example Home Apps: `plugin://plugin.video.kodihome/?action=app_group&group_name=Home+Apps`
