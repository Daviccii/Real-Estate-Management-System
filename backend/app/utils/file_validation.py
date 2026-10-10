"""
File Upload Security

Content-based (magic bytes) file type validation, size limits, and safe
filename generation for user uploads. The client-supplied filename and
Content-Type header are never trusted - only the actual bytes decide
whether a file is accepted and how it is stored.
"""
import re
import uuid

from app.config.settings import settings


class FileValidationError(ValueError):
    """Raised when an upload fails security validation."""


# (prefix bytes at offset 0, required bytes at offset 8 or None, media type, extension)
_ALLOWED_SIGNATURES = [
    (b"\xff\xd8\xff", None, "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", None, "image/png", ".png"),
    (b"GIF87a", None, "image/gif", ".gif"),
    (b"GIF89a", None, "image/gif", ".gif"),
    (b"RIFF", b"WEBP", "image/webp", ".webp"),
    (b"%PDF-", None, "application/pdf", ".pdf"),
]

# Generated storage names look like: 32-char hex + approved extension
_STORED_NAME_PATTERN = re.compile(r"^[a-f0-9]{32}\.(jpg|png|gif|webp|pdf)$")

_MEDIA_TYPES_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}


def detect_file_type(content: bytes) -> tuple[str, str]:
    """
    Identify a file's type from its magic bytes.

    Returns:
        (media_type, extension)

    Raises:
        FileValidationError: if the content does not match an allowed type.
    """
    for prefix, offset_bytes, media_type, extension in _ALLOWED_SIGNATURES:
        if content.startswith(prefix):
            if offset_bytes is not None and content[8:12] != offset_bytes:
                continue
            return media_type, extension

    # Explicitly reject common disguise formats before the generic failure
    head = content[:300].lstrip()
    if head.startswith((b"<", b"<!DOCTYPE", b"<?xml", b"MZ", b"\x7fELF")):
        raise FileValidationError("Archives, executables, and markup files are not allowed")

    raise FileValidationError("Unrecognized file type. Allowed: JPEG, PNG, GIF, WebP, PDF")


def validate_upload(file_bytes: bytes) -> tuple[str, str, str]:
    """
    Validate an uploaded file and derive a safe stored filename.

    Args:
        file_bytes: Raw uploaded content

    Returns:
        (media_type, extension, stored_filename)

    Raises:
        FileValidationError: on empty, oversized, or disallowed content.
    """
    if not file_bytes:
        raise FileValidationError("Uploaded file is empty")

    if len(file_bytes) > settings.MAX_UPLOAD_FILE_BYTES:
        max_mb = settings.MAX_UPLOAD_FILE_BYTES // (1024 * 1024)
        raise FileValidationError(f"File exceeds the maximum allowed size of {max_mb} MB")

    media_type, extension = detect_file_type(file_bytes)

    # Random storage name: prevents path traversal, collisions, and
    # information leaking through original filenames.
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    return media_type, extension, stored_filename


def is_safe_stored_filename(filename: str) -> bool:
    """Check that a filename is one this module could have generated."""
    return bool(_STORED_NAME_PATTERN.fullmatch(filename))


def media_type_for_stored_filename(filename: str) -> str:
    """Content type to serve a stored file with (defaults to octet-stream)."""
    extension = "." + filename.rsplit(".", 1)[-1].lower()
    return _MEDIA_TYPES_BY_EXTENSION.get(extension, "application/octet-stream")
