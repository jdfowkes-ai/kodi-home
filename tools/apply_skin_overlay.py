#!/usr/bin/env python3
"""Apply the Kodi Home information-panel overlay to an Arctic Fuse 3.4.18 checkout."""

import argparse
import base64
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_VERSION = "3.4.18"
CUSTOM_ADDON_ID = "skin.arctic.fuse.3.kodihome"
CUSTOM_ADDON_NAME = "Arctic Fuse 3 Kodi Home"
CUSTOM_ADDON_VERSION = "0.5.2"
OVERLAY_FILES = (
    Path("1080i/Includes_Info.xml"),
    Path("shortcuts/skinvariables-startup.json"),
)
BADGE_BUNDLE = PROJECT_ROOT / "skin/assets/uk-certification-badges.json"


def skin_version(addon_xml: Path) -> str:
    root = ET.parse(addon_xml).getroot()
    return root.attrib.get("version", "")


def validate_overlay() -> tuple[dict[Path, bytes], dict[str, bytes]]:
    overlay_files = {}
    for relative_path in OVERLAY_FILES:
        source = PROJECT_ROOT / "skin" / relative_path
        payload = source.read_bytes()
        if relative_path.suffix == ".xml":
            ET.fromstring(payload)
        elif relative_path.suffix == ".json":
            json.loads(payload)
        overlay_files[relative_path] = payload

    bundle = json.loads(BADGE_BUNDLE.read_text(encoding="utf-8"))
    assets = {
        f"media/flags/color/mpaa/{name}": base64.b64decode(encoded, validate=True)
        for name, encoded in bundle["files"].items()
    }
    return overlay_files, assets



def apply_app_tile_overlay(skin_root: Path) -> None:
    """Add a grey, white-logo presentation to Kodi Home app tiles in square views."""
    views_file = skin_root / "1080i/Includes_Views_List.xml"
    source = views_file.read_text(encoding="utf-8")
    start_marker = '    <include name="View_Media_Square">'
    end_marker = '    <include name="View_Media_Poster">'
    start = source.find(start_marker)
    end = source.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0 or source.find(start_marker, start + 1) >= 0:
        raise RuntimeError("Could not locate the expected Arctic Fuse square tile include")

    block = source[start:end]
    group_open = '        <control type="group">'
    if block.count(group_open) < 1 or "KodiHome.AppTile" in block:
        raise RuntimeError("Arctic Fuse square tile include has an unexpected structure")
    block = block.replace(
        group_open,
        group_open + '\n            <visible>!String.IsEqual(ListItem.Property(KodiHome.AppTile),true)</visible>',
        1,
    )

    tile = """        <control type="group">
            <visible>String.IsEqual(ListItem.Property(KodiHome.AppTile),true)</visible>
            <height>612</height>
            <width>612</width>
            <control type="image">
                <texture colordiffuse="D9707070">common/white.png</texture>
            </control>
            <control type="image">
                <width>80%</width>
                <height>42%</height>
                <centerleft>50%</centerleft>
                <centertop>50%</centertop>
                <aspectratio>keep</aspectratio>
                <texture>$INFO[ListItem.Art(clearlogo)]</texture>
                <visible>String.IsEqual(ListItem.Property(KodiHome.HasClearLogo),true)</visible>
            </control>
            <control type="label">
                <width>85%</width>
                <height>120</height>
                <centerleft>50%</centerleft>
                <centertop>50%</centertop>
                <align>center</align>
                <aligny>center</aligny>
                <font>font_main_bold</font>
                <textcolor>FFFFFFFF</textcolor>
                <label>$INFO[ListItem.Label]</label>
                <visible>!String.IsEqual(ListItem.Property(KodiHome.HasClearLogo),true)</visible>
            </control>
        </control>
"""
    closing = '    </include>'
    close_at = block.rfind(closing)
    if close_at < 0:
        raise RuntimeError("Could not close the Arctic Fuse square tile include")
    block = block[:close_at] + tile + block[close_at:]
    updated = source[:start] + block + source[end:]
    ET.fromstring(updated)
    views_file.write_text(updated, encoding="utf-8")



def apply_app_background_overlay(skin_root: Path) -> None:
    """Use Kodi Home app or library item fanart as the focused background."""
    images_file = skin_root / "1080i/Includes_Images.xml"
    source = images_file.read_text(encoding="utf-8")
    marker = '    <variable name="Image_Foreground">'
    if source.count(marker) != 1:
        raise RuntimeError("Could not locate the Arctic Fuse foreground image variable")
    if "KodiHome.AppTile" in source[source.index(marker):source.index("</variable>", source.index(marker))]:
        raise RuntimeError("Kodi Home app background rule is already present")
    values = (
        '        <value condition="String.IsEqual(Container.ListItem.Property(KodiHome.LibraryItem),true) '
        '+ !String.IsEmpty(Container.ListItem.Art(fanart))">'
        '$INFO[Container.ListItem.Art(fanart)]</value>\n'
        '        <value condition="String.IsEqual(Container.ListItem.Property(KodiHome.AppTile),true) '
        '+ !String.IsEmpty(Container.ListItem.Art(fanart))">'
        '$INFO[Container.ListItem.Art(fanart)]</value>\n'
    )
    updated = source.replace(marker, marker + "\n" + values, 1)
    ET.fromstring(updated)
    images_file.write_text(updated, encoding="utf-8")




def apply_app_background_slideshow_overlay(skin_root: Path) -> None:
    """Rotate app-specific background images while that app is focused."""
    background_file = skin_root / "1080i/Includes_Background.xml"
    source = background_file.read_text(encoding="utf-8")
    start_marker = '    <include name="Background_Artwork">'
    end_marker = '    <include name="Background_Blur_Quadrants">'
    start = source.find(start_marker)
    end = source.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise RuntimeError("Could not locate the Arctic Fuse artwork background include")

    block = source[start:end]
    if "KodiHome.BackgroundFolder" in block:
        raise RuntimeError("Kodi Home app background slideshow is already present")
    insert_at = block.rfind("        </definition>")
    if insert_at < 0:
        raise RuntimeError("Could not locate the Arctic Fuse artwork definition end")

    slideshow = """            <control type="multiimage">
                <top>0</top>
                <right>0</right>
                <height>flixart_size_h</height>
                <width>flixart_size_w</width>
                <aspectratio scalediffuse="false">scale</aspectratio>
                <imagepath>$INFO[Container.ListItem.Property(KodiHome.BackgroundFolder)]</imagepath>
                <timeperimage>8000</timeperimage>
                <fadetime>1200</fadetime>
                <randomize>true</randomize>
                <loop>yes</loop>
                <visible>String.IsEqual(Container.ListItem.Property(KodiHome.AppTile),true) + !String.IsEmpty(Container.ListItem.Property(KodiHome.BackgroundFolder))</visible>
                <include>Background_NotVideo</include>
            </control>
"""
    block = block[:insert_at] + slideshow + block[insert_at:]
    updated = source[:start] + block + source[end:]
    ET.fromstring(updated)
    background_file.write_text(updated, encoding="utf-8")



def apply_library_widget_preset(skin_root: Path) -> None:
    """Add an opt-in Kodi Home Library preset to Arctic Fuse's setup wizard."""
    wizard_file = skin_root / "1080i/Dialog_DialogSetupWizard.xml"
    wizard = wizard_file.read_text(encoding="utf-8")
    library_card = """            <include content="DialogSetupWizard_Widget_Preset">
                <param name="preset">library</param>
                <param name="icon">film</param>
                <param name="label">$LOCALIZE[31761]</param>
                <param name="label2">$LOCALIZE[31764]</param>
            </include>"""
    kodihome_card = """            <include content="DialogSetupWizard_Widget_Preset">
                <param name="preset">kodihome</param>
                <param name="icon">film</param>
                <param name="label">Kodi Home Library</param>
                <param name="label2">Movies and TV library widgets</param>
                <param name="visible">System.AddonIsEnabled(plugin.video.kodihome)</param>
            </include>"""
    if wizard.count(library_card) != 1 or '<param name="preset">kodihome</param>' in wizard:
        raise RuntimeError("Could not safely locate the Arctic Fuse widget preset list")
    wizard = wizard.replace(library_card, library_card + "\n" + kodihome_card, 1)
    ET.fromstring(wizard)
    wizard_file.write_text(wizard, encoding="utf-8")

    preset_file = skin_root / "shortcuts/builtins/skinvariables-setupwizard-preset.json"
    setup = json.loads(preset_file.read_text(encoding="utf-8"))
    parts = setup.get("parts", {})
    if "preset_library" not in parts or "preset_kodihome" in parts:
        raise RuntimeError("Could not safely extend the Arctic Fuse setup wizard preset")
    parts["preset_kodihome"] = parts["preset_library"]
    preset_file.write_text(json.dumps(setup, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")

    library_dir = skin_root / "shortcuts/presets/library"
    kodihome_dir = skin_root / "shortcuts/presets/kodihome"
    if not library_dir.is_dir() or kodihome_dir.exists():
        raise RuntimeError("Could not safely create the Kodi Home Library widget preset")
    shutil.copytree(library_dir, kodihome_dir)

    widget_rows = {
        "skinvariables-shortcut-1101widgets.json": {
            "label": "Kodi Home Movies Library",
            "path": "plugin://plugin.video.kodihome/?action=library_items&media_type=movie",
        },
        "skinvariables-shortcut-1102widgets.json": {
            "label": "Kodi Home TV Library",
            "path": "plugin://plugin.video.kodihome/?action=library_items&media_type=tvshow",
        },
    }
    for filename, row in widget_rows.items():
        widget_file = kodihome_dir / filename
        widgets = json.loads(widget_file.read_text(encoding="utf-8"))
        widgets.insert(0, {
            "label": row["label"],
            "icon": "",
            "path": row["path"],
            "target": "videos",
            "widget_style": "Poster",
        })
        widget_file.write_text(json.dumps(widgets, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")



def apply_keep_changes_focus_overlay(skin_root: Path) -> None:
    """Give Kodi's Keep Changes button the initial focus after a skin switch."""
    dialog_file = skin_root / "1080i/DialogConfirm.xml"
    source = dialog_file.read_text(encoding="utf-8")
    marker = "<window>"
    focused = '<window>\n    <defaultcontrol always="true">9010</defaultcontrol>'
    if source.count(marker) != 1 or "<defaultcontrol" in source:
        raise RuntimeError("Could not safely set the Arctic Fuse confirmation dialog focus")
    updated = source.replace(marker, focused, 1)
    ET.fromstring(updated)
    dialog_file.write_text(updated, encoding="utf-8")


def apply_overlay(skin_root: Path) -> None:
    addon_xml = skin_root / "addon.xml"
    if not addon_xml.is_file():
        raise FileNotFoundError(f"No addon.xml in skin source: {skin_root}")
    actual_version = skin_version(addon_xml)
    if actual_version != BASE_VERSION:
        raise RuntimeError(
            f"Expected Arctic Fuse {BASE_VERSION}; found {actual_version or 'unknown'}. "
            "Refusing to overlay an unverified skin base."
        )

    overlay_files, assets = validate_overlay()

    for relative_path, payload in overlay_files.items():
        destination = skin_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

    apply_app_tile_overlay(skin_root)
    apply_keep_changes_focus_overlay(skin_root)
    apply_app_background_overlay(skin_root)
    apply_app_background_slideshow_overlay(skin_root)

    for relative_path, payload in assets.items():
        destination = skin_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

    addon_tree = ET.parse(addon_xml)
    addon_root = addon_tree.getroot()
    addon_root.set("id", CUSTOM_ADDON_ID)
    addon_root.set("name", CUSTOM_ADDON_NAME)
    addon_root.set("version", CUSTOM_ADDON_VERSION)
    addon_tree.write(addon_xml, encoding="UTF-8", xml_declaration=True)

    print(
        f"Applied Kodi Home info and app tile overlays to Arctic Fuse {BASE_VERSION}: "
        f"{len(overlay_files)} files and {len(assets)} certificate badges."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skin_root",
        type=Path,
        help="Path to a complete Arctic Fuse 3.4.18 source checkout",
    )
    args = parser.parse_args()
    try:
        apply_overlay(args.skin_root.resolve())
    except (ET.ParseError, OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
