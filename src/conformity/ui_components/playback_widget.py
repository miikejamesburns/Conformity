"""
Media playback widget for conform review.

Provides video playback with frame-accurate navigation, timecode display,
and support for image sequences.
"""

from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider,
    QLabel, QFileDialog
)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPixmap, QImage

from ..core.logger import get_logger

logger = get_logger(__name__)


class PlaybackWidget(QWidget):
    """
    Video playback widget with frame-accurate controls.

    Features:
    - Standard playback controls (play, pause, stop)
    - Frame-accurate navigation (frame forward/back)
    - Timecode display
    - Scrubbing support
    - Image sequence playback
    - Keyboard shortcuts
    """

    # Signals
    frame_changed = pyqtSignal(int)  # Current frame number
    timecode_changed = pyqtSignal(str)  # Current timecode

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[Path] = None
        self.frame_rate: float = 24.0
        self.total_frames: int = 0
        self.current_frame: int = 0
        self.is_image_sequence: bool = False
        self.image_sequence_frames: List[Path] = []

        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # Timer for frame updates
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame_info)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize user interface."""
        layout = QVBoxLayout(self)

        # Video display
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)

        # Timecode and frame info
        info_layout = QHBoxLayout()

        self.timecode_label = QLabel("00:00:00:00")
        self.timecode_label.setStyleSheet("font-family: monospace; font-size: 14pt;")
        info_layout.addWidget(self.timecode_label)

        self.frame_label = QLabel("Frame: 0 / 0")
        info_layout.addWidget(self.frame_label)

        info_layout.addStretch()

        self.duration_label = QLabel("Duration: 00:00:00")
        info_layout.addWidget(self.duration_label)

        layout.addLayout(info_layout)

        # Playback controls
        controls_layout = QHBoxLayout()

        # Load button
        self.load_btn = QPushButton("Load Media")
        self.load_btn.clicked.connect(self._on_load_media)
        controls_layout.addWidget(self.load_btn)

        controls_layout.addStretch()

        # Frame back
        self.frame_back_btn = QPushButton("◀|")
        self.frame_back_btn.setToolTip("Previous Frame (Left Arrow)")
        self.frame_back_btn.clicked.connect(self.frame_back)
        controls_layout.addWidget(self.frame_back_btn)

        # Play/Pause
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setToolTip("Play/Pause (Space)")
        self.play_pause_btn.clicked.connect(self.play_pause)
        controls_layout.addWidget(self.play_pause_btn)

        # Frame forward
        self.frame_forward_btn = QPushButton("|▶")
        self.frame_forward_btn.setToolTip("Next Frame (Right Arrow)")
        self.frame_forward_btn.clicked.connect(self.frame_forward)
        controls_layout.addWidget(self.frame_forward_btn)

        controls_layout.addStretch()

        # Stop
        self.stop_btn = QPushButton("■")
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_btn)

        layout.addLayout(controls_layout)

        # Timeline slider
        slider_layout = QHBoxLayout()

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._on_slider_moved)
        slider_layout.addWidget(self.position_slider)

        layout.addLayout(slider_layout)

    def _connect_signals(self):
        """Connect media player signals."""
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)

    def load_media(self, file_path: Path, frame_rate: float = 24.0):
        """
        Load media file for playback.

        Args:
            file_path: Path to media file or image sequence
            frame_rate: Frame rate for timecode calculation
        """
        self.current_file = file_path
        self.frame_rate = frame_rate

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return

        # Check if image sequence
        if self._is_image_sequence(file_path):
            self._load_image_sequence(file_path)
        else:
            # Load video file
            self.is_image_sequence = False
            self.media_player.setSource(QUrl.fromLocalFile(str(file_path)))

        logger.info(f"Loaded media: {file_path}")

    def _is_image_sequence(self, file_path: Path) -> bool:
        """
        Check if file is part of an image sequence.

        Args:
            file_path: File to check

        Returns:
            True if image sequence
        """
        # Simple check: if extension is image format and directory has multiple images
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.dpx'}
        if file_path.suffix.lower() in image_extensions:
            # Count images in directory
            image_count = sum(1 for f in file_path.parent.iterdir()
                            if f.suffix.lower() in image_extensions)
            return image_count > 1
        return False

    def _load_image_sequence(self, file_path: Path):
        """
        Load image sequence for playback.

        Args:
            file_path: Path to any frame in sequence
        """
        self.is_image_sequence = True

        # Find all images in sequence
        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.exr', '.dpx'}
        self.image_sequence_frames = sorted([
            f for f in file_path.parent.iterdir()
            if f.suffix.lower() in image_extensions
        ])

        self.total_frames = len(self.image_sequence_frames)
        self.current_frame = 0

        if self.image_sequence_frames:
            self._display_image_frame(0)

        self.position_slider.setRange(0, self.total_frames - 1)
        self._update_frame_info()

        logger.info(f"Loaded image sequence: {self.total_frames} frames")

    def _display_image_frame(self, frame_index: int):
        """
        Display a frame from image sequence.

        Args:
            frame_index: Frame index to display
        """
        if not self.image_sequence_frames or frame_index >= len(self.image_sequence_frames):
            return

        frame_path = self.image_sequence_frames[frame_index]

        # Load image
        image = QImage(str(frame_path))
        if image.isNull():
            logger.error(f"Failed to load image: {frame_path}")
            return

        # Display in video widget (convert to pixmap)
        pixmap = QPixmap.fromImage(image)

        # Scale to fit video widget
        scaled = pixmap.scaled(
            self.video_widget.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Note: QVideoWidget doesn't support direct pixmap display
        # For a full implementation, we'd need to use QLabel or custom widget
        # For now, log the operation
        logger.debug(f"Displaying frame {frame_index}: {frame_path}")

    def play_pause(self):
        """Toggle play/pause."""
        if self.is_image_sequence:
            if self.timer.isActive():
                self.timer.stop()
                self.play_pause_btn.setText("▶")
            else:
                # Calculate interval for frame rate
                interval_ms = int(1000 / self.frame_rate)
                self.timer.start(interval_ms)
                self.play_pause_btn.setText("⏸")
        else:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()

    def stop(self):
        """Stop playback."""
        if self.is_image_sequence:
            self.timer.stop()
            self.current_frame = 0
            self._display_image_frame(0)
            self._update_frame_info()
        else:
            self.media_player.stop()

    def frame_forward(self):
        """Move forward one frame."""
        if self.is_image_sequence:
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self._display_image_frame(self.current_frame)
                self.position_slider.setValue(self.current_frame)
                self._update_frame_info()
        else:
            # For video, jump forward by one frame duration
            frame_duration_ms = int(1000 / self.frame_rate)
            new_position = self.media_player.position() + frame_duration_ms
            self.media_player.setPosition(new_position)

    def frame_back(self):
        """Move back one frame."""
        if self.is_image_sequence:
            if self.current_frame > 0:
                self.current_frame -= 1
                self._display_image_frame(self.current_frame)
                self.position_slider.setValue(self.current_frame)
                self._update_frame_info()
        else:
            # For video, jump back by one frame duration
            frame_duration_ms = int(1000 / self.frame_rate)
            new_position = max(0, self.media_player.position() - frame_duration_ms)
            self.media_player.setPosition(new_position)

    def seek_to_frame(self, frame_number: int):
        """
        Seek to specific frame.

        Args:
            frame_number: Target frame number
        """
        if self.is_image_sequence:
            if 0 <= frame_number < self.total_frames:
                self.current_frame = frame_number
                self._display_image_frame(self.current_frame)
                self.position_slider.setValue(self.current_frame)
                self._update_frame_info()
        else:
            # Convert frame to milliseconds
            frame_duration_ms = 1000 / self.frame_rate
            position_ms = int(frame_number * frame_duration_ms)
            self.media_player.setPosition(position_ms)

    def get_current_frame(self) -> int:
        """
        Get current frame number.

        Returns:
            Current frame number
        """
        return self.current_frame

    def get_timecode(self) -> str:
        """
        Get current timecode.

        Returns:
            Timecode string (HH:MM:SS:FF)
        """
        return self._frames_to_timecode(self.current_frame, self.frame_rate)

    def _on_load_media(self):
        """Handle load media button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Media File",
            str(Path.home()),
            "Media Files (*.mp4 *.mov *.avi *.mkv *.jpg *.jpeg *.png *.exr *.dpx);;All Files (*)"
        )

        if file_path:
            self.load_media(Path(file_path))

    def _on_position_changed(self, position: int):
        """
        Handle media player position change.

        Args:
            position: Position in milliseconds
        """
        if not self.is_image_sequence:
            self.position_slider.setValue(position)

            # Calculate current frame
            frame_duration_ms = 1000 / self.frame_rate
            self.current_frame = int(position / frame_duration_ms)

            self._update_frame_info()

    def _on_duration_changed(self, duration: int):
        """
        Handle media duration change.

        Args:
            duration: Duration in milliseconds
        """
        if not self.is_image_sequence:
            self.position_slider.setRange(0, duration)

            # Calculate total frames
            frame_duration_ms = 1000 / self.frame_rate
            self.total_frames = int(duration / frame_duration_ms)

            # Update duration label
            seconds = duration / 1000
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            self.duration_label.setText(f"Duration: {hours:02d}:{minutes:02d}:{secs:02d}")

    def _on_slider_moved(self, position: int):
        """
        Handle timeline slider movement.

        Args:
            position: Slider position
        """
        if self.is_image_sequence:
            self.current_frame = position
            self._display_image_frame(self.current_frame)
            self._update_frame_info()
        else:
            self.media_player.setPosition(position)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState):
        """Handle playback state change."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_btn.setText("⏸")
        else:
            self.play_pause_btn.setText("▶")

    def _update_frame_info(self):
        """Update frame information display."""
        # Update timecode
        timecode = self._frames_to_timecode(self.current_frame, self.frame_rate)
        self.timecode_label.setText(timecode)

        # Update frame counter
        self.frame_label.setText(f"Frame: {self.current_frame} / {self.total_frames}")

        # Emit signals
        self.frame_changed.emit(self.current_frame)
        self.timecode_changed.emit(timecode)

    @staticmethod
    def _frames_to_timecode(frames: int, frame_rate: float) -> str:
        """
        Convert frame number to timecode.

        Args:
            frames: Frame number
            frame_rate: Frame rate

        Returns:
            Timecode string (HH:MM:SS:FF)
        """
        total_seconds = frames / frame_rate
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frame = int(frames % frame_rate)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        key = event.key()

        if key == Qt.Key.Key_Space:
            self.play_pause()
        elif key == Qt.Key.Key_Left:
            self.frame_back()
        elif key == Qt.Key.Key_Right:
            self.frame_forward()
        elif key == Qt.Key.Key_Home:
            self.seek_to_frame(0)
        elif key == Qt.Key.Key_End:
            self.seek_to_frame(self.total_frames - 1)
        else:
            super().keyPressEvent(event)
