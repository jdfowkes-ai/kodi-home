"""Owned Umbrella .strm shortcut storage.

Only files created and recorded by this module are eligible for deletion.
This module does not modify Kodi's video database or scan sources.
"""
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse


class ManagedShortcuts:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = self.root / "managed-shortcuts.json"

    def _records(self):
        if not self.manifest.exists():
            return {}
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid managed shortcut manifest")
        return data

    def _save(self, records):
        temp = self.manifest.with_suffix(".json.tmp")
        temp.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(str(temp), str(self.manifest))

    def _path(self, media_type, identifier):
        if media_type not in ("movie", "episode"):
            raise ValueError("Only movie and episode shortcuts are supported")
        if not identifier or len(identifier) > 512:
            raise ValueError("Invalid stable identifier")
        digest = hashlib.sha256((media_type + ":" + identifier).encode("utf-8")).hexdigest()
        folder = self.root / ("movies" if media_type == "movie" else "episodes")
        return folder / (digest + ".strm")

    def add(self, media_type, identifier, umbrella_url):
        parsed = urlparse(umbrella_url)
        if parsed.scheme != "plugin" or parsed.netloc != "plugin.video.umbrella":
            raise ValueError("Only Umbrella plugin URLs can be saved")
        if "\\n" in umbrella_url or "\\r" in umbrella_url:
            raise ValueError("Invalid shortcut URL")
        path = self._path(media_type, identifier)
        records = self._records()
        key = media_type + ":" + identifier
        if key in records:
            if records[key] != str(path) or not path.is_file():
                raise ValueError("Managed shortcut record does not match existing file")
            if path.read_text(encoding="utf-8").strip() != umbrella_url:
                raise ValueError("Existing shortcut content differs")
            return str(path)
        if path.exists():
            raise FileExistsError("Unmanaged shortcut already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(umbrella_url + "\\n")
        records[key] = str(path)
        self._save(records)
        return str(path)

    def remove(self, media_type, identifier):
        path = self._path(media_type, identifier)
        records = self._records()
        key = media_type + ":" + identifier
        if records.get(key) != str(path):
            raise ValueError("Shortcut is not owned by Kodi Home")
        if not path.is_file() or path.is_symlink():
            raise ValueError("Managed shortcut is missing or unsafe")
        content = path.read_text(encoding="utf-8").strip()
        parsed = urlparse(content)
        if parsed.scheme != "plugin" or parsed.netloc != "plugin.video.umbrella":
            raise ValueError("Shortcut is no longer an Umbrella link")
        path.unlink()
        del records[key]
        self._save(records)
        return str(path)
