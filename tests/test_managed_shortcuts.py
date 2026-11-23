"""Regression tests for ownership-safe Umbrella shortcut storage."""
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "addon" / "resources" / "lib" / "kodihome" / "managed_shortcuts.py"
spec = importlib.util.spec_from_file_location("managed_shortcuts", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ManagedShortcuts = module.ManagedShortcuts


class ManagedShortcutsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.manager = ManagedShortcuts(Path(self.temp.name) / "owned")
        self.url = "plugin://plugin.video.umbrella/?action=play&tmdb=123"

    def test_add_and_remove(self):
        path = Path(self.manager.add("movie", "tmdb:123", self.url))
        self.assertEqual(path.read_text(), self.url + "\n")
        self.assertEqual(self.manager.add("movie", "tmdb:123", self.url), str(path))
        self.assertEqual(self.manager.remove("movie", "tmdb:123"), str(path))
        self.assertFalse(path.exists())

    def test_reject_unmanaged_file(self):
        path = self.manager._path("movie", "tmdb:123")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.url)
        with self.assertRaises(FileExistsError):
            self.manager.add("movie", "tmdb:123", self.url)
        with self.assertRaises(ValueError):
            self.manager.remove("movie", "tmdb:123")
        self.assertTrue(path.exists())

    def test_reject_non_umbrella_url_and_newlines(self):
        for url in ("https://example.com/", self.url + "\nother", self.url + "\rother"):
            with self.assertRaises(ValueError):
                self.manager.add("movie", "tmdb:123", url)

    def test_reject_modified_shortcut_on_remove(self):
        path = Path(self.manager.add("movie", "tmdb:123", self.url))
        path.write_text("https://example.com/")
        with self.assertRaises(ValueError):
            self.manager.remove("movie", "tmdb:123")
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
