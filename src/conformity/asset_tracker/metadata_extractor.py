"""
Metadata extraction for media files.

Extracts technical metadata from video, image, and audio files
using ffprobe, PIL, and other tools.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib

from ..core.logger import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """
    Extract technical metadata from media files.

    Uses ffprobe for video/audio, PIL for images.
    """

    # Supported file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.mxf', '.r3d', '.braw', '.ari'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.dpx', '.cr2', '.nef'}
    AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aac', '.flac', '.aif', '.aiff'}

    def __init__(self):
        """Initialize metadata extractor."""
        self.ffprobe_available = self._check_ffprobe()

    def _check_ffprobe(self) -> bool:
        """Check if ffprobe is available."""
        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                timeout=5
            )
            available = result.returncode == 0
            if not available:
                logger.warning("ffprobe not found - video metadata extraction will be limited")
            return available
        except Exception:
            logger.warning("ffprobe not available")
            return False

    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a file.

        Args:
            file_path: Path to media file

        Returns:
            Dictionary of metadata
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {}

        metadata = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'extension': file_path.suffix.lower()
        }

        # Add checksum
        metadata['checksum'] = self.calculate_checksum(file_path)

        # Extract based on file type
        ext = file_path.suffix.lower()

        if ext in self.VIDEO_EXTENSIONS:
            metadata.update(self.extract_video_metadata(file_path))
        elif ext in self.IMAGE_EXTENSIONS:
            metadata.update(self.extract_image_metadata(file_path))
        elif ext in self.AUDIO_EXTENSIONS:
            metadata.update(self.extract_audio_metadata(file_path))

        return metadata

    def extract_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract video metadata using ffprobe.

        Args:
            file_path: Path to video file

        Returns:
            Video metadata dictionary
        """
        if not self.ffprobe_available:
            return {'error': 'ffprobe not available'}

        try:
            # Run ffprobe to get JSON output
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"ffprobe failed for {file_path}")
                return {'error': 'ffprobe failed'}

            data = json.loads(result.stdout)

            metadata = {}

            # Extract format information
            if 'format' in data:
                fmt = data['format']
                metadata['duration'] = float(fmt.get('duration', 0))
                metadata['bit_rate'] = int(fmt.get('bit_rate', 0))
                metadata['format_name'] = fmt.get('format_name', '')
                metadata['format_long_name'] = fmt.get('format_long_name', '')

            # Extract video stream information
            video_stream = None
            audio_stream = None

            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream

            if video_stream:
                metadata['width'] = int(video_stream.get('width', 0))
                metadata['height'] = int(video_stream.get('height', 0))
                metadata['codec'] = video_stream.get('codec_name', '')
                metadata['codec_long_name'] = video_stream.get('codec_long_name', '')
                metadata['pixel_format'] = video_stream.get('pix_fmt', '')

                # Frame rate calculation
                r_frame_rate = video_stream.get('r_frame_rate', '0/1')
                if '/' in r_frame_rate:
                    num, den = map(int, r_frame_rate.split('/'))
                    if den > 0:
                        metadata['frame_rate'] = round(num / den, 3)

                # Color information
                metadata['color_space'] = video_stream.get('color_space', '')
                metadata['color_primaries'] = video_stream.get('color_primaries', '')
                metadata['color_transfer'] = video_stream.get('color_transfer', '')
                metadata['color_range'] = video_stream.get('color_range', '')

                # Bit depth
                if 'bits_per_raw_sample' in video_stream:
                    metadata['bit_depth'] = int(video_stream['bits_per_raw_sample'])

            if audio_stream:
                metadata['audio_codec'] = audio_stream.get('codec_name', '')
                metadata['audio_channels'] = int(audio_stream.get('channels', 0))
                metadata['audio_sample_rate'] = int(audio_stream.get('sample_rate', 0))
                metadata['audio_bit_depth'] = audio_stream.get('bits_per_sample', 0)

            return metadata

        except subprocess.TimeoutExpired:
            logger.error(f"ffprobe timeout for {file_path}")
            return {'error': 'timeout'}
        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            return {'error': str(e)}

    def extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract image metadata.

        Args:
            file_path: Path to image file

        Returns:
            Image metadata dictionary
        """
        metadata = {}

        # Try with PIL first
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['mode'] = img.mode
                metadata['format'] = img.format

                # Get EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        metadata['exif'] = {k: str(v) for k, v in exif.items() if isinstance(v, (str, int, float))}

        except ImportError:
            logger.warning("PIL not available for image metadata")
        except Exception as e:
            logger.debug(f"PIL extraction failed, trying ffprobe: {e}")

        # Fall back to ffprobe for advanced formats (EXR, DPX, etc.)
        if self.ffprobe_available and not metadata:
            try:
                result = subprocess.run(
                    [
                        'ffprobe',
                        '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_streams',
                        str(file_path)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get('streams'):
                        stream = data['streams'][0]
                        metadata['width'] = int(stream.get('width', 0))
                        metadata['height'] = int(stream.get('height', 0))
                        metadata['pixel_format'] = stream.get('pix_fmt', '')
                        metadata['color_space'] = stream.get('color_space', '')

            except Exception as e:
                logger.debug(f"ffprobe image extraction failed: {e}")

        return metadata

    def extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract audio metadata using ffprobe.

        Args:
            file_path: Path to audio file

        Returns:
            Audio metadata dictionary
        """
        if not self.ffprobe_available:
            return {'error': 'ffprobe not available'}

        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    str(file_path)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {'error': 'ffprobe failed'}

            data = json.loads(result.stdout)

            metadata = {}

            # Format info
            if 'format' in data:
                fmt = data['format']
                metadata['duration'] = float(fmt.get('duration', 0))
                metadata['bit_rate'] = int(fmt.get('bit_rate', 0))

            # Audio stream info
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    metadata['audio_codec'] = stream.get('codec_name', '')
                    metadata['audio_channels'] = int(stream.get('channels', 0))
                    metadata['audio_sample_rate'] = int(stream.get('sample_rate', 0))
                    metadata['audio_bit_depth'] = stream.get('bits_per_sample', 0)
                    break

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            return {'error': str(e)}

    def calculate_checksum(self, file_path: Path, algorithm: str = 'md5') -> str:
        """
        Calculate file checksum.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (md5, sha256)

        Returns:
            Hexadecimal checksum string
        """
        try:
            if algorithm == 'md5':
                hasher = hashlib.md5()
            elif algorithm == 'sha256':
                hasher = hashlib.sha256()
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)

            return hasher.hexdigest()

        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""

    @staticmethod
    def is_media_file(file_path: Path) -> bool:
        """
        Check if file is a supported media type.

        Args:
            file_path: Path to file

        Returns:
            True if supported media file
        """
        ext = file_path.suffix.lower()
        return ext in (
            MetadataExtractor.VIDEO_EXTENSIONS |
            MetadataExtractor.IMAGE_EXTENSIONS |
            MetadataExtractor.AUDIO_EXTENSIONS
        )

    @staticmethod
    def get_asset_type(file_path: Path) -> str:
        """
        Determine asset type from file extension.

        Args:
            file_path: Path to file

        Returns:
            Asset type string (video, image, audio, other)
        """
        ext = file_path.suffix.lower()

        if ext in MetadataExtractor.VIDEO_EXTENSIONS:
            return 'video'
        elif ext in MetadataExtractor.IMAGE_EXTENSIONS:
            return 'image'
        elif ext in MetadataExtractor.AUDIO_EXTENSIONS:
            return 'audio'
        else:
            return 'other'
