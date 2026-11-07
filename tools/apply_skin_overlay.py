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
CUSTOM_ADDON_VERSION = "0.1.0"
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
        f"Applied Kodi Home info overlay to Arctic Fuse {BASE_VERSION}: "
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
