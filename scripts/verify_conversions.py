"""Exercise actual Office conversion with the bundled LibreOffice distribution."""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pymupdf  # noqa: E402

from app.backend.application.conversion_service import ConversionService  # noqa: E402
from app.backend.application.progress import ProgressReporter  # noqa: E402
from app.backend.config import BackendConfig  # noqa: E402
from app.backend.domain.enums import OperationType  # noqa: E402
from app.backend.domain.models import ConversionJob  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("libreoffice", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()
    progress = ProgressReporter(lambda: False, lambda *_: None, lambda *_: None)
    service = ConversionService(
        BackendConfig(
            libreoffice_executable=str(args.libreoffice.resolve()),
            libreoffice_timeout_seconds=args.timeout_seconds,
        )
    )
    with tempfile.TemporaryDirectory(prefix="docuconvert-verification-") as directory:
        root = Path(directory)
        sources = []
        for index in range(2):
            source = root / f"source-{index}" / "Laporan.2026.odt"
            source.parent.mkdir()
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
                archive.writestr(
                    "META-INF/manifest.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    "<manifest:manifest "
                    'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
                    '<manifest:file-entry manifest:full-path="/" '
                    'manifest:media-type="application/vnd.oasis.opendocument.text"/>'
                    '<manifest:file-entry manifest:full-path="content.xml" '
                    'manifest:media-type="text/xml"/></manifest:manifest>',
                )
                archive.writestr(
                    "content.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    "<office:document-content "
                    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
                    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
                    'office:version="1.2"><office:body><office:text>'
                    f"<text:p>Dokumen {index + 1}</text:p>"
                    "</office:text></office:body></office:document-content>",
                )
            sources.append(source)
        for name, files, options, expected in (
            ("single", sources[:1], {"output_name": "Nama baru.pdf"}, ["Nama baru.pdf"]),
            ("batch-default", sources, {}, ["Laporan.2026_1.pdf", "Laporan.2026_2.pdf"]),
            (
                "batch-custom",
                sources,
                {"output_name": "Custom.pdf"},
                ["Custom-001.pdf", "Custom-002.pdf"],
            ),
        ):
            output = root / name
            output.mkdir()
            result = service.run(
                ConversionJob(OperationType.WORD_TO_PDF, files, output, options), progress
            )
            assert [path.name for path in result.output_files] == expected, result
            for path in result.output_files:
                with pymupdf.open(path) as document:
                    assert document.page_count == 1
                    assert "Dokumen" in document[0].get_text()
            print(f"Office conversion OK: {name}, {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
