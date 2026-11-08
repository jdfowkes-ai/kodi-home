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

Each app keeps its Android icon and can have a custom clear logo and fanart image selected from Kodi's configured file sources. If no custom fanart is set, Kodi Home can choose random matching titles' fanart from the Kodi video library using studio metadata (including Umbrella `.strm` entries). It caches up to twelve matching images per app for the skin's rotating background, so the brand slideshow can work without a manually selected image folder. This matches brand-related Kodi library studio metadata, including Disney, Pixar, Marvel, Lucasfilm, Apple Studios, Amazon Studios, BBC, ITV, Channel 4, Channel 5, Paramount, Nickelodeon, discovery+, NOW/Sky, and YouTube Originals. Matching depends on what studio metadata is present in your library. If Kodi has no matching title or studio metadata, the manual image/folder remains the fallback. Use the app context menu's **Choose rotating background folder** action to select a folder of brand-related images for that app. **Clear rotating background folder** returns it to the single fanart image. The Arctic Fuse overlay now styles only the square app tile with a slightly transparent mid-grey background and a centred clear logo. If no clear logo is set, it shows the app name in white. As focus moves across the widget row, Arctic Fuse now prioritizes the selected app item's own fanart for the background, ahead of TMDb Helper background properties. If a rotating folder is set, Arctic Fuse shuffles its images every eight seconds with a crossfade; otherwise it uses the single fanart image. Kodi skin textures support animated GIFs, so a folder can also include a compatible GIF.

Automatic online retrieval of branded shows or movie artwork, and video splash clips, remain pending. User-selected rotating folders use images already available in a Kodi picture source. Automatically matched folders use fanart already present in Kodi's video library. This feature is source code only; installation and Shield verification have not happened yet.

## Group widgets

Group folders and widgets show only the apps in that group. If a group is empty, it shows one **Add apps to [group]** tile; that tile disappears after apps are added. Use **Add installed app** from the Apps list to add apps to a group. Rename or delete a group from its context menu in the Apps list; rename, change artwork, or remove an app from the app tile context menu.

## Paths

- Apps group list: `plugin://plugin.video.kodihome/?action=apps`
- A group as a widget, for example Home Apps: `plugin://plugin.video.kodihome/?action=app_group&group_name=Home+Apps`
