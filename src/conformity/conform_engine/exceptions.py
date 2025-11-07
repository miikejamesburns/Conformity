"""
Exception classes for conform operations.

This module defines custom exceptions for handling errors during
timeline import, export, and conform operations.
"""


class ConformError(Exception):
    """Base exception for conform operations."""
    pass


class MediaNotFoundError(ConformError):
    """Raised when referenced media files cannot be found."""

    def __init__(self, media_path: str, clip_name: str = None):
        self.media_path = media_path
        self.clip_name = clip_name
        message = f"Media file not found: {media_path}"
        if clip_name:
            message = f"Media file not found for clip '{clip_name}': {media_path}"
        super().__init__(message)


class UnsupportedFeatureError(ConformError):
    """Raised when timeline contains unsupported features."""

    def __init__(self, feature: str, details: str = None):
        self.feature = feature
        self.details = details
        message = f"Unsupported timeline feature: {feature}"
        if details:
            message += f" - {details}"
        super().__init__(message)


class InvalidTimecodeError(ConformError):
    """Raised when timecode ranges are invalid."""

    def __init__(self, timecode: str, reason: str = None):
        self.timecode = timecode
        self.reason = reason
        message = f"Invalid timecode: {timecode}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class ImportError(ConformError):
    """Raised when timeline import fails."""

    def __init__(self, file_path: str, reason: str = None):
        self.file_path = file_path
        self.reason = reason
        message = f"Failed to import timeline from: {file_path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class ExportError(ConformError):
    """Raised when timeline export fails."""

    def __init__(self, file_path: str, format: str = None, reason: str = None):
        self.file_path = file_path
        self.format = format
        self.reason = reason
        message = f"Failed to export timeline to: {file_path}"
        if format:
            message += f" (format: {format})"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class AdapterNotFoundError(ConformError):
    """Raised when OTIO adapter for format is not available."""

    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
        message = f"OTIO adapter not found: {adapter_name}"
        super().__init__(message)
