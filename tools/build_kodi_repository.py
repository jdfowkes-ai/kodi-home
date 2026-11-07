#!/usr/bin/env python3
"""Build Kodi Home packages and a Kodi-compatible add-on repository site."""

import hashlib
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_URL = "https://jdfowkes-ai.github.io/kodi-home"


def addon_metadata(path):
    root = ET.parse(path).getroot()
    return root, root.attrib["id"], root.attrib["version"]


def package_addon(source, output, addon_id):
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file() and ".git" not in path.parts:
                archive.write(path, Path(addon_id) / path.relative_to(source))


def repository_addon_xml():
    root = ET.Element("addon", {
        "id": "repository.kodihome",
        "name": "Kodi Home Repository",
        "version": "1.0.1",
        "provider-name": "jdfowkes-ai",
    })
    requires = ET.SubElement(root, "requires")
    ET.SubElement(requires, "import", {"addon": "xbmc.addon", "version": "12.0.0"})
    extension = ET.SubElement(root, "extension", {
        "point": "xbmc.addon.repository",
        "name": "Kodi Home Repository",
    })
    directory = ET.SubElement(extension, "dir")
    ET.SubElement(directory, "info", {"compressed": "false"}).text = PAGES_URL + "/addons.xml"
    ET.SubElement(directory, "checksum", {"verify": "md5"}).text = PAGES_URL + "/addons.xml.md5"
    ET.SubElement(directory, "datadir").text = PAGES_URL + "/"
    ET.SubElement(directory, "hashes").text = "false"
    metadata = ET.SubElement(root, "extension", {"point": "xbmc.addon.metadata"})
    ET.SubElement(metadata, "summary", {"lang": "en_GB"}).text = "Kodi Home add-ons"
    ET.SubElement(metadata, "description", {"lang": "en_GB"}).text = (
        "Install and update Kodi Home for local playback lists, Shield app groups, "
        "and the Arctic Fuse visual package."
    )
    ET.SubElement(metadata, "platform").text = "all"
    return root


def build(site_dir, skin_source):
    site_dir.mkdir(parents=True, exist_ok=True)
    addon_source = PROJECT_ROOT / "addon"
    plugin_xml, plugin_id, plugin_version = addon_metadata(addon_source / "addon.xml")
    skin_xml, skin_id, skin_version = addon_metadata(skin_source / "addon.xml")

    plugin_zip = site_dir / (plugin_id + "-" + plugin_version + ".zip")
    skin_zip = site_dir / skin_id / (skin_id + "-" + skin_version + ".zip")
    package_addon(addon_source, plugin_zip, plugin_id)
    package_addon(skin_source, skin_zip, skin_id)

    # Kodi resolves downloads as <datadir>/<addon id>/<package zip>.
    # Keep a root copy of the small plugin ZIP for manual installation, but
    # publish the larger skin ZIP only in its repository directory to avoid
    # duplicating it in the Pages artifact.
    plugin_package_dir = site_dir / plugin_id
    plugin_package_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plugin_zip, plugin_package_dir / plugin_zip.name)

    repo_id = "repository.kodihome"
    repo_version = "1.0.1"
    repo_root = PROJECT_ROOT / "repository" / repo_id
    repo_root.mkdir(parents=True, exist_ok=True)
    repo_xml = repository_addon_xml()
    ET.indent(repo_xml, space="    ")
    repo_xml_path = repo_root / "addon.xml"
    ET.ElementTree(repo_xml).write(repo_xml_path, encoding="UTF-8", xml_declaration=True)
    repo_zip = site_dir / (repo_id + "-" + repo_version + ".zip")
    package_addon(repo_root, repo_zip, repo_id)

    addons = ET.Element("addons")
    for source_xml in (addon_source / "addon.xml", skin_source / "addon.xml", repo_xml_path):
        addons.append(ET.parse(source_xml).getroot())
    ET.indent(addons, space="    ")
    addons_path = site_dir / "addons.xml"
    ET.ElementTree(addons).write(addons_path, encoding="UTF-8", xml_declaration=True)
    checksum = hashlib.md5(addons_path.read_bytes()).hexdigest()
    (site_dir / "addons.xml.md5").write_text(checksum, encoding="ascii")

    links = (
        repo_zip.name,
        plugin_zip.name,
        skin_id + "/" + skin_zip.name,
        "addons.xml",
        "addons.xml.md5",
    )
    newline = chr(10)
    items = newline.join(
        '      <li><a href="{0}">{0}</a></li>'.format(name)
        for name in links
    )
    (site_dir / "index.html").write_text(
        '<!doctype html>' + newline
        + '<html lang="en">' + newline
        + '<head><meta charset="utf-8"><title>Kodi Home Repository</title></head>' + newline
        + '<body>' + newline
        + '<h1>Kodi Home Repository</h1>' + newline
        + '<p>Add this HTTPS source in Kodi: <code>' + PAGES_URL + '/</code></p>' + newline
        + '<p>Install the Kodi Home Repository ZIP below, then install Kodi Home from '
        + 'Kodi Home Repository.</p>' + newline
        + '<ul>' + newline + items + newline + '</ul>' + newline
        + '</body>' + newline + '</html>' + newline,
        encoding="utf-8",
    )
    print("Built repository site for %s %s and %s %s" % (
        plugin_id, plugin_version, skin_id, skin_version
    ))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_kodi_repository.py SITE_DIRECTORY SKIN_SOURCE_DIRECTORY")
    build(Path(sys.argv[1]), Path(sys.argv[2]))
