"""
Timeline editor module for advanced editing operations.

This module provides comprehensive timeline editing functionality including:
- Ripple, roll, slip, and slide editing
- Split, trim, copy, paste operations
- Track management
- Gap management
- Undo/redo support
"""

from .edit_operations import (
    TimelineEditor,
    EditOperation,
    RippleEdit,
    RollEdit,
    SlipEdit,
    SlideEdit,
)
from .clip_operations import (
    split_clip,
    trim_clip,
    copy_clip,
    paste_clip,
    duplicate_clip,
    delete_clip,
)
from .track_operations import (
    add_track,
    remove_track,
    reorder_tracks,
    merge_tracks,
)
from .gap_utils import (
    find_gaps,
    remove_gaps,
    insert_gap,
    close_gap,
)

__all__ = [
    'TimelineEditor',
    'EditOperation',
    'RippleEdit',
    'RollEdit',
    'SlipEdit',
    'SlideEdit',
    'split_clip',
    'trim_clip',
    'copy_clip',
    'paste_clip',
    'duplicate_clip',
    'delete_clip',
    'add_track',
    'remove_track',
    'reorder_tracks',
    'merge_tracks',
    'find_gaps',
    'remove_gaps',
    'insert_gap',
    'close_gap',
]
