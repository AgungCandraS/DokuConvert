"""Stable operation and job-state identifiers."""

from enum import StrEnum


class OperationType(StrEnum):
    WORD_TO_PDF = "word_to_pdf"
    EXCEL_TO_PDF = "excel_to_pdf"
    POWERPOINT_TO_PDF = "powerpoint_to_pdf"
    ODT_TO_PDF = "odt_to_pdf"
    PDF_TO_DOCX = "pdf_to_word"
    IMAGE_TO_PDF = "image_to_pdf"
    PDF_TO_IMAGE = "pdf_to_image"
    MERGE_PDF = "merge_pdf"
    SPLIT_PDF = "split_pdf"
    COMPRESS_PDF = "compress_pdf"
    ROTATE_PDF = "rotate_pdf"
    DELETE_PAGES = "delete_pages"
    WATERMARK_PDF = "watermark_pdf"
    PROTECT_PDF = "protect_pdf"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
