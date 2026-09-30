"""Packaging must preserve every runtime file and refuse to overwrite user files."""

import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.package_portable import main, package_portable


class PortablePackageTests(unittest.TestCase):
    def test_cli_works_with_windows_console_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _ = self.source(root)
            target = root / "windows-console.zip"
            stream = io.BytesIO()
            console = io.TextIOWrapper(stream, encoding="cp1252", write_through=True)
            with (
                patch("sys.argv", ["package_portable.py", str(source), str(target)]),
                patch("sys.stdout", console),
            ):
                self.assertEqual(main(), 0)
            self.assertIn(b"ZIP siap digunakan", stream.getvalue())
            self.assertTrue(target.is_file())

    def source(self, root):
        source = root / "portable"
        files = {
            "DocuConvert/DocuConvert.exe": b"app" * 1000,
            "DocuConvert/_internal/library.bin": bytes(range(256)) * 200,
            "DocuConvert/tools/LibreOffice/program/soffice.exe": b"runtime" * 2000,
            "DocuConvert/LICENSE": b"License notice",
            "DocuConvert/.config": b"Keep hidden files",
            "README-PORTABLE.txt": b"Petunjuk DocuConvert",
        }
        for name, data in files.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return source, files

    def test_archive_preserves_all_bytes_and_has_valid_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, files = self.source(root)
            target = root / "DocuConvert.zip"
            raw, compressed = package_portable(source, target)
            self.assertEqual(raw, sum(len(data) for data in files.values()))
            self.assertLess(compressed, raw / 2)
            with zipfile.ZipFile(target) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), set(files))
                for name, data in files.items():
                    self.assertEqual(archive.read(name), data)
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual((root / "DocuConvert.zip.sha256").read_text().split()[0], digest)
            self.assertEqual(list(root.glob("*.part")), [])

    def test_existing_archive_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _ = self.source(root)
            target = root / "existing.zip"
            target.write_bytes(b"keep existing file")
            with self.assertRaises(FileExistsError):
                package_portable(source, target)
            self.assertEqual(target.read_bytes(), b"keep existing file")

    def test_archive_cannot_be_written_inside_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source, _ = self.source(Path(directory))
            with self.assertRaises(ValueError):
                package_portable(source, source / "nested.zip")

    def test_incomplete_portable_build_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                package_portable(root, root.parent / "incomplete.zip")
