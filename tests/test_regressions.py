"""Regression coverage for output names, watermark geometry, and verified updates."""

import hashlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pymupdf

from app.backend.application.conversion_service import ConversionService
from app.backend.application.progress import ProgressReporter
from app.backend.converters.pdf_operations import PdfOperationsConverter
from app.backend.domain.enums import OperationType
from app.backend.domain.models import ConversionJob
from app.backend.infrastructure.update_service import (
    DOWNLOAD_PREFIX,
    UpdateRelease,
    UpdateService,
    platform_asset,
    version_tuple,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def reporter():
    return ProgressReporter(lambda: False, lambda *_: None, lambda *_: None)


class OutputTests(unittest.TestCase):
    def test_pdf_compression_keeps_document_content(self):
        import random

        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Original.pdf"
            pixels = random.Random(42).randbytes(800 * 1000 * 3)
            image = Image.frombytes("RGB", (800, 1000), pixels)
            stream = io.BytesIO()
            image.save(stream, format="PNG")
            with pymupdf.open() as document:
                page = document.new_page(width=400, height=600)
                page.insert_text((20, 30), "Isi dokumen tetap terbaca")
                page.insert_image(pymupdf.Rect(20, 60, 220, 310), stream=stream.getvalue())
                document.save(source)
            original_bytes = source.read_bytes()
            result = ConversionService().run(
                ConversionJob(
                    OperationType.COMPRESS_PDF,
                    [source],
                    root,
                    {"output_name": "Kompres.pdf", "quality": "balanced"},
                ),
                reporter(),
            )
            self.assertTrue(result.success)
            self.assertEqual(source.read_bytes(), original_bytes)
            self.assertLess(result.output_files[0].stat().st_size, source.stat().st_size)
            with pymupdf.open(result.output_files[0]) as document:
                self.assertEqual(document.page_count, 1)
                self.assertIn("Isi dokumen tetap terbaca", document[0].get_text())
                self.assertTrue(document[0].get_images())

    def test_compression_success_notification_uses_app_name(self):
        from PySide6.QtWidgets import QApplication, QLabel

        from app.ui.job_panel import JobPanel
        from app.ui.tool_catalog import TOOL_BY_KEY

        application = QApplication.instance() or QApplication([])
        panel = JobPanel(TOOL_BY_KEY["compress_pdf"].name, open_output=False)
        panel.set_completed([])
        self.assertIn("DocuConvert selesai mengompres PDF", panel.status_label.text())
        self.assertNotIn("LibreOffice", panel.status_label.text())
        panel.deleteLater()
        office = JobPanel(TOOL_BY_KEY["word_to_pdf"].name, libreoffice_path="soffice.exe")
        labels = [label.text() for label in office.findChildren(QLabel)]
        self.assertTrue(any("DocuConvert siap" in text for text in labels))
        self.assertFalse(any("LibreOffice" in text for text in labels))
        office.deleteLater()
        application.processEvents()

    def test_conversion_publishes_custom_name_and_preserves_existing_file(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Foto.png"
            Image.new("RGB", (80, 120), "white").save(source)
            existing = root / "Hasil.pdf"
            existing.write_bytes(b"keep existing")
            service = ConversionService()
            result = service.run(
                ConversionJob(
                    OperationType.IMAGE_TO_PDF, [source], root, {"output_name": "Hasil.pdf"}
                ),
                reporter(),
            )
            self.assertTrue(result.success)
            self.assertEqual(result.output_files[0].name, "Hasil_1.pdf")
            self.assertEqual(existing.read_bytes(), b"keep existing")
            with pymupdf.open(result.output_files[0]) as document:
                self.assertEqual(document.page_count, 1)

    def test_numbered_outputs_preserve_dots_in_prefix(self):
        for operation, options, names in (
            (OperationType.PDF_TO_IMAGE, {}, ["Laporan.2026-001.png", "Laporan.2026-002.png"]),
            (
                OperationType.SPLIT_PDF,
                {"mode": "ranges", "page_ranges": "1,2"},
                ["Laporan.2026_1.pdf", "Laporan.2026_2.pdf"],
            ),
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                outputs = [
                    root / f"file{index}{Path(name).suffix}" for index, name in enumerate(names)
                ]
                for output in outputs:
                    output.write_bytes(b"content")
                job = ConversionJob(operation, [], root, {**options, "output_name": "Laporan.2026"})
                renamed = ConversionService._apply_output_name(job, outputs)
                self.assertEqual([p.name for p in renamed], names)

    def test_custom_batch_name_and_dotted_single_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            originals = [root / "report.pdf", root / "other.pdf"]
            for index, path in enumerate(originals):
                path.write_bytes(str(index).encode())
            job = ConversionJob(
                OperationType.WORD_TO_PDF, [], root, {"output_name": "Laporan.2026.pdf"}
            )
            outputs = ConversionService._apply_output_name(job, originals)
            self.assertEqual(
                [p.name for p in outputs], ["Laporan.2026-001.pdf", "Laporan.2026-002.pdf"]
            )
            self.assertEqual([p.read_bytes() for p in outputs], [b"0", b"1"])
            job.options["output_name"] = "Revisi.2026"
            renamed = ConversionService._apply_output_name(job, outputs[:1])
            self.assertEqual(renamed[0].name, "Revisi.2026.pdf")

    def test_ui_office_name_edit_reaches_request(self):
        from PySide6.QtWidgets import QApplication

        from app.ui.job_panel import JobPanel
        from app.ui.tool_catalog import TOOL_BY_KEY

        application = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Laporan.2026.docx"
            source.touch()
            panel = JobPanel(TOOL_BY_KEY["word_to_pdf"].name, [str(source)], directory)
            self.assertFalse(panel.output_name.isHidden())
            self.assertEqual(panel.output_name.text(), "Laporan.2026.pdf")
            panel.output_name.setText("Hasil baru.pdf")
            self.assertEqual(panel._create_request()["output_name"], "Hasil baru.pdf")
            panel._has_custom_name = True
            other = Path(directory) / "Other.docx"
            other.touch()
            panel._add_files([str(other)])
            self.assertEqual(panel.output_name.text(), "Hasil baru.pdf")
            panel._has_custom_name = False
            panel._sync_order_from_list()
            self.assertEqual(panel.output_name.text(), "")
            panel.deleteLater()
            application.processEvents()

    def test_watermark_visible_center_for_rotated_cropped_pages(self):
        for rotation in (0, 90, 180, 270):
            for position in ("center", "diagonal", "bottom"):
                for text in ("INTERNAL", "Dokumen sangat panjang " * 6):
                    with self.subTest(rotation=rotation, position=position, text=text[:20]):
                        with tempfile.TemporaryDirectory() as directory:
                            root = Path(directory)
                            source = root / "input.pdf"
                            with pymupdf.open() as document:
                                page = document.new_page(width=600, height=800)
                                page.set_cropbox(pymupdf.Rect(20, 30, 570, 760))
                                page.set_rotation(rotation)
                                document.save(source)
                            job = ConversionJob(
                                OperationType.WATERMARK_PDF,
                                [source],
                                root,
                                {"text": text, "position": position},
                            )
                            outputs = PdfOperationsConverter._watermark(job, reporter(), root)
                            with pymupdf.open(outputs[0]) as document:
                                page = document[0]
                                spans = [
                                    span
                                    for block in page.get_text("dict")["blocks"]
                                    for line in block.get("lines", [])
                                    for span in line["spans"]
                                ]
                                self.assertTrue(spans)
                                bbox = pymupdf.Rect(spans[0]["bbox"]) * page.rotation_matrix
                                self.assertAlmostEqual(
                                    (bbox.x0 + bbox.x1) / 2, page.rect.width / 2, delta=1
                                )
                                if position != "bottom":
                                    self.assertAlmostEqual(
                                        (bbox.y0 + bbox.y1) / 2, page.rect.height / 2, delta=1
                                    )
                                else:
                                    self.assertAlmostEqual(bbox.y1, page.rect.height - 32, delta=1)
                                self.assertGreaterEqual(bbox.x0, -1)
                                self.assertLessEqual(bbox.x1, page.rect.width + 1)


class UpdateTests(unittest.TestCase):
    def test_background_check_delivers_result_and_releases_worker(self):
        from PySide6.QtCore import QEventLoop, QObject, QTimer
        from PySide6.QtWidgets import QApplication

        from app.ui.controllers.update_controller import UpdateController

        application = QApplication.instance() or QApplication([])
        parent = QObject()
        controller = UpdateController(parent)
        loop = QEventLoop()
        result = []
        controller.checked.connect(lambda release, manual: result.append((release, manual)))
        controller.busy_changed.connect(lambda busy: None if busy else loop.quit())
        with patch("app.ui.controllers.update_controller.UpdateService.check", return_value=None):
            controller.check(manual=True)
            QTimer.singleShot(3000, loop.quit)
            loop.exec()
            self.assertFalse(controller.busy)
            self.assertEqual(result, [(None, True)])
            controller.close()
            application.processEvents()

    def test_update_launcher_targets_existing_windows_install(self):
        from app.ui.controllers.update_controller import launch_update

        package = Path("D:/download/DocuConvert-Windows-x64.exe")
        with (
            patch("app.ui.controllers.update_controller.sys.frozen", True, create=True),
            patch("app.ui.controllers.update_controller.sys.platform", "win32"),
            patch(
                "app.ui.controllers.update_controller.sys.executable",
                "D:/Apps/DocuConvert/DocuConvert.exe",
            ),
            patch("app.ui.controllers.update_controller.subprocess.Popen") as launch,
            patch(
                "app.ui.controllers.update_controller.subprocess.DETACHED_PROCESS", 8, create=True
            ),
            patch(
                "app.ui.controllers.update_controller.subprocess.CREATE_NEW_PROCESS_GROUP",
                512,
                create=True,
            ),
        ):
            self.assertTrue(launch_update(package))
            command = launch.call_args.args[0]
            expected_directory = Path("D:/Apps/DocuConvert/DocuConvert.exe").resolve().parent
            self.assertIn(f"/DIR={expected_directory}", command)
            self.assertIn("/UPDATE", command)
            self.assertIn("/NORESTART", command)

    def test_untrusted_download_url_is_rejected(self):
        payload = self.payload()
        payload["assets"][0]["browser_download_url"] = "https://example.com/package.exe"
        with (
            patch(
                "app.backend.infrastructure.update_service.urlopen",
                return_value=io.BytesIO(json.dumps(payload).encode()),
            ),
            patch(
                "app.backend.infrastructure.update_service.platform_asset",
                return_value="DocuConvert-Windows-x64.exe",
            ),
        ):
            with self.assertRaises(ValueError):
                UpdateService().check()

    def test_versions_and_platforms(self):
        self.assertGreater(version_tuple("v0.10.0"), version_tuple("0.9.9"))
        for invalid in ("1", "1.0.0-rc1", "../../1.0.0"):
            with self.assertRaises(ValueError):
                version_tuple(invalid)
        self.assertEqual(platform_asset("Windows", "AMD64"), "DocuConvert-Windows-x64.exe")
        self.assertIn("Apple-Silicon", platform_asset("Darwin", "arm64"))
        self.assertIn("Intel", platform_asset("Darwin", "x86_64"))
        self.assertIn("amd64", platform_asset("Linux", "x86_64"))
        with self.assertRaises(ValueError):
            platform_asset("Linux", "aarch64")

    def payload(self, version="v0.2.0"):
        return {
            "tag_name": version,
            "assets": [
                {
                    "name": "DocuConvert-Windows-x64.exe",
                    "browser_download_url": DOWNLOAD_PREFIX
                    + version
                    + "/DocuConvert-Windows-x64.exe",
                    "size": 7,
                    "digest": "sha256:" + "a" * 64,
                }
            ],
        }

    def test_check_new_same_and_older_release(self):
        for version, available in (("v0.2.0", True), ("v0.1.1", False), ("v0.1.0", False)):
            with (
                patch(
                    "app.backend.infrastructure.update_service.urlopen",
                    return_value=io.BytesIO(json.dumps(self.payload(version)).encode()),
                ),
                patch(
                    "app.backend.infrastructure.update_service.platform_asset",
                    return_value="DocuConvert-Windows-x64.exe",
                ),
            ):
                self.assertEqual(UpdateService().check("0.1.1") is not None, available)

    def test_no_release_and_offline(self):
        with patch(
            "app.backend.infrastructure.update_service.urlopen",
            side_effect=HTTPError("url", 404, "Not found", {}, None),
        ):
            self.assertIsNone(UpdateService().check())
        with patch(
            "app.backend.infrastructure.update_service.urlopen", side_effect=OSError("offline")
        ):
            with self.assertRaises(OSError):
                UpdateService().check()

    def test_checksum_fallback(self):
        payload = self.payload()
        payload["assets"][0].pop("digest")
        payload["assets"].append(
            {
                "name": "SHA256SUMS.txt",
                "browser_download_url": DOWNLOAD_PREFIX + "v0.2.0/SHA256SUMS.txt",
            }
        )
        responses = [
            io.BytesIO(json.dumps(payload).encode()),
            io.BytesIO(("b" * 64 + "  DocuConvert-Windows-x64.exe\n").encode()),
        ]
        with (
            patch("app.backend.infrastructure.update_service.urlopen", side_effect=responses),
            patch(
                "app.backend.infrastructure.update_service.platform_asset",
                return_value="DocuConvert-Windows-x64.exe",
            ),
        ):
            self.assertEqual(UpdateService().check().sha256, "b" * 64)

    def test_verified_download_and_corruption_cleanup(self):
        data = b"package"
        release = UpdateRelease(
            "0.2.0",
            "DocuConvert-Windows-x64.exe",
            DOWNLOAD_PREFIX + "v0.2.0/package",
            len(data),
            hashlib.sha256(data).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch(
                    "app.backend.infrastructure.update_service.user_data_directory",
                    return_value=root,
                ),
                patch(
                    "app.backend.infrastructure.update_service.urlopen",
                    return_value=io.BytesIO(data),
                ),
            ):
                progress = []
                target = UpdateService().download(release, progress.append, lambda: False)
                self.assertEqual(target.read_bytes(), data)
                self.assertEqual(progress[-1], 100)
            before = set((root / "updates").iterdir())
            for payload, cancelled in (
                (b"corrupt", False),
                (data, True),
                (b"too long package", False),
            ):
                with (
                    patch(
                        "app.backend.infrastructure.update_service.user_data_directory",
                        return_value=root,
                    ),
                    patch(
                        "app.backend.infrastructure.update_service.urlopen",
                        return_value=io.BytesIO(payload),
                    ),
                ):
                    with self.assertRaises((ValueError, InterruptedError)):
                        UpdateService().download(
                            release, lambda *_: None, lambda stop=cancelled: stop
                        )
                self.assertEqual(set((root / "updates").iterdir()), before)


if __name__ == "__main__":
    unittest.main()
