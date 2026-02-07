"""File system watcher for live codemap updates."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from ..utils.config import Config, load_config
from ..utils.file_utils import get_language, should_exclude

logger = logging.getLogger(__name__)

# Optional watchdog import
try:
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object
    Observer = None


class CodemapEventHandler(FileSystemEventHandler):
    """Handles file system events for codemap updates."""

    def __init__(
        self,
        root: Path,
        config: Config,
        on_change: Callable[[Path, str], None],
        debounce_seconds: float = 0.5,
    ):
        """Initialize the event handler.

        Args:
            root: Root directory being watched.
            config: CodeMap configuration.
            on_change: Callback for file changes. Args: (filepath, event_type).
            debounce_seconds: Time to wait before processing changes.
        """
        super().__init__()
        self.root = root
        self.config = config
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds

        # Debouncing state
        self._pending_changes: dict[str, tuple[Path, str, float]] = {}
        self._lock = threading.Lock()
        self._debounce_timer: Optional[threading.Timer] = None

    def _should_process(self, path: str) -> bool:
        """Check if the file should be processed.

        Args:
            path: Absolute file path.

        Returns:
            True if file should be processed.
        """
        try:
            filepath = Path(path)

            # Skip directories
            if filepath.is_dir():
                return False

            # Skip .codemap directory
            try:
                rel_path = filepath.relative_to(self.root).as_posix()
            except ValueError:
                return False

            if rel_path.startswith(".codemap"):
                return False

            # Check if it's a supported language
            if get_language(filepath) is None:
                return False

            # Check exclude patterns
            if should_exclude(rel_path, self.config.exclude_patterns):
                return False

            return True
        except Exception:
            return False

    def _schedule_change(self, filepath: Path, event_type: str) -> None:
        """Schedule a change to be processed after debounce period.

        Args:
            filepath: Path to the changed file.
            event_type: Type of change (created, modified, deleted).
        """
        with self._lock:
            key = str(filepath)
            self._pending_changes[key] = (filepath, event_type, time.time())

            # Cancel existing timer
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()

            # Schedule new timer
            self._debounce_timer = threading.Timer(
                self.debounce_seconds,
                self._process_pending_changes,
            )
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _process_pending_changes(self) -> None:
        """Process all pending changes."""
        with self._lock:
            changes = list(self._pending_changes.values())
            self._pending_changes.clear()
            self._debounce_timer = None

        for filepath, event_type, _ in changes:
            try:
                self.on_change(filepath, event_type)
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")

    def on_created(self, event: "FileSystemEvent") -> None:
        """Handle file creation."""
        if not event.is_directory and self._should_process(event.src_path):
            self._schedule_change(Path(event.src_path), "created")

    def on_modified(self, event: "FileSystemEvent") -> None:
        """Handle file modification."""
        if not event.is_directory and self._should_process(event.src_path):
            self._schedule_change(Path(event.src_path), "modified")

    def on_deleted(self, event: "FileSystemEvent") -> None:
        """Handle file deletion."""
        # For deletions, we can't check if it's a supported file anymore
        # so we'll process it and let the indexer handle it
        if not event.is_directory:
            filepath = Path(event.src_path)
            if get_language(filepath) is not None:
                try:
                    rel_path = filepath.relative_to(self.root).as_posix()
                    # Skip .codemap directory
                    if rel_path.startswith(".codemap"):
                        return
                    if not should_exclude(rel_path, self.config.exclude_patterns):
                        self._schedule_change(filepath, "deleted")
                except ValueError:
                    pass

    def on_moved(self, event: "FileSystemEvent") -> None:
        """Handle file move/rename."""
        # Treat as delete + create
        if not event.is_directory:
            # Delete old location
            src_path = Path(event.src_path)
            if get_language(src_path) is not None:
                try:
                    rel_path = src_path.relative_to(self.root).as_posix()
                    # Skip .codemap directory
                    if rel_path.startswith(".codemap"):
                        return
                    if not should_exclude(rel_path, self.config.exclude_patterns):
                        self._schedule_change(src_path, "deleted")
                except ValueError:
                    pass

            # Create at new location
            if self._should_process(event.dest_path):
                self._schedule_change(Path(event.dest_path), "created")


class CodeMapWatcher:
    """Watches a directory for changes and updates the codemap."""

    def __init__(
        self,
        root: Path,
        on_update: Optional[Callable[[str, int], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
        debounce_seconds: float = 0.5,
    ):
        """Initialize the watcher.

        Args:
            root: Root directory to watch.
            on_update: Callback when a file is updated. Args: (filepath, symbols_changed).
            on_error: Callback when an error occurs. Args: (filepath, exception).
            debounce_seconds: Time to wait before processing changes.

        Raises:
            ImportError: If watchdog is not installed.
            FileNotFoundError: If no codemap exists.
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog is required for watch mode. "
                "Install with: pip install watchdog"
            )

        self.root = root.resolve()
        self.on_update = on_update
        self.on_error = on_error
        self.debounce_seconds = debounce_seconds

        # Load config and indexer
        self.config = load_config(self.root)

        # Import here to avoid circular imports
        from .indexer import Indexer

        self.indexer = Indexer.load_existing(self.root)

        # Set up observer
        self._observer: Optional["Observer"] = None
        self._running = False

    def _handle_change(self, filepath: Path, event_type: str) -> None:
        """Handle a file change event.

        Args:
            filepath: Path to the changed file.
            event_type: Type of change.
        """
        try:
            rel_path = filepath.relative_to(self.root).as_posix()
        except ValueError:
            rel_path = filepath.as_posix()

        try:
            if event_type == "deleted":
                # Remove from index
                removed = self.indexer.map_store.remove_file(rel_path)
                if removed:
                    self.indexer.map_store.update_stats()
                    self.indexer.map_store.save()
                    if self.on_update:
                        self.on_update(rel_path, 0)
            else:
                # Update file (created or modified)
                result = self.indexer.update_file(filepath)
                if self.on_update:
                    self.on_update(rel_path, result.get("symbols_changed", 0))

        except Exception as e:
            logger.error(f"Error updating {rel_path}: {e}")
            if self.on_error:
                self.on_error(rel_path, e)

    def start(self) -> None:
        """Start watching for changes."""
        if self._running:
            return

        handler = CodemapEventHandler(
            root=self.root,
            config=self.config,
            on_change=self._handle_change,
            debounce_seconds=self.debounce_seconds,
        )

        self._observer = Observer()
        self._observer.schedule(handler, str(self.root), recursive=True)
        self._observer.start()
        self._running = True

    def stop(self) -> None:
        """Stop watching for changes."""
        if not self._running or self._observer is None:
            return

        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if the watcher is running."""
        return self._running

    def __enter__(self) -> "CodeMapWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def watch_directory(
    root: Path,
    on_update: Optional[Callable[[str, int], None]] = None,
    on_error: Optional[Callable[[str, Exception], None]] = None,
    debounce_seconds: float = 0.5,
) -> CodeMapWatcher:
    """Create and start a directory watcher.

    Args:
        root: Root directory to watch.
        on_update: Callback when a file is updated.
        on_error: Callback when an error occurs.
        debounce_seconds: Time to wait before processing changes.

    Returns:
        Running CodeMapWatcher instance.
    """
    watcher = CodeMapWatcher(
        root=root,
        on_update=on_update,
        on_error=on_error,
        debounce_seconds=debounce_seconds,
    )
    watcher.start()
    return watcher
