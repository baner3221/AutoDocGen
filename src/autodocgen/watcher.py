"""
File watcher for incremental documentation updates.
"""

from pathlib import Path
from typing import Callable, Optional
import time
import fnmatch

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from autodocgen.config import Config


class CppFileEventHandler(FileSystemEventHandler):
    """
    Handles file system events for C++ files.

    Triggers documentation regeneration when files change.
    """

    def __init__(
        self,
        config: Config,
        on_change: Callable[[Path], None],
    ):
        """
        Initialize the event handler.

        Args:
            config: AutoDocGen configuration
            on_change: Callback when a file changes
        """
        super().__init__()
        self.config = config
        self.on_change = on_change
        self.extensions = set(config.parser.supported_extensions)
        self.exclude_patterns = config.parser.exclude_patterns
        self._debounce: dict[str, float] = {}
        self._debounce_seconds = 2.0  # Wait 2 seconds before processing

    def _should_process(self, path: Path) -> bool:
        """Check if a file should be processed."""
        if path.suffix not in self.extensions:
            return False

        # Check exclude patterns
        try:
            relative = path.relative_to(self.config.codebase_path)
            for pattern in self.exclude_patterns:
                if fnmatch.fnmatch(str(relative), pattern):
                    return False
        except ValueError:
            return False

        return True

    def _debounced(self, path: str) -> bool:
        """Check if the event is debounced."""
        now = time.time()
        last = self._debounce.get(path, 0)

        if now - last < self._debounce_seconds:
            return True

        self._debounce[path] = now
        return False

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if not self._should_process(path):
            return

        if self._debounced(str(path)):
            return

        self.on_change(path)

    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if not self._should_process(path):
            return

        if self._debounced(str(path)):
            return

        self.on_change(path)


class FileWatcher:
    """
    Watches a codebase for changes and triggers incremental updates.
    """

    def __init__(self, config: Config):
        """
        Initialize the file watcher.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.observer: Optional[Observer] = None
        self._running = False

        # Import here to avoid circular imports
        from autodocgen.analyzer import CodebaseAnalyzer
        self.analyzer = CodebaseAnalyzer(config)

    def start(self) -> None:
        """Start watching the codebase."""
        from rich.console import Console
        console = Console()

        # Initial scan
        console.print("[bold]Performing initial documentation scan...[/]")
        self.analyzer.scan_codebase()
        self.analyzer.parse_all()
        self.analyzer.generate_documentation()
        console.print("[green]Initial documentation complete.[/]")

        # Set up watcher
        handler = CppFileEventHandler(
            self.config,
            on_change=self._handle_change,
        )

        self.observer = Observer()
        self.observer.schedule(
            handler,
            str(self.config.codebase_path),
            recursive=True,
        )

        self.observer.start()
        self._running = True

        console.print(f"\n[bold green]Watching:[/] {self.config.codebase_path}")
        console.print("[dim]Press Ctrl+C to stop[/]\n")

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop watching."""
        self._running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()

        self.analyzer.close()

    def _handle_change(self, path: Path) -> None:
        """Handle a file change."""
        from rich.console import Console
        console = Console()

        console.print(f"[yellow]Change detected:[/] {path.name}")

        try:
            # Re-parse the file
            analysis = self.analyzer.parser.parse_file(path)
            self.analyzer._analyses[path] = analysis
            self.analyzer.context_builder.register_analysis(analysis)

            # Regenerate documentation for this file
            self.analyzer._document_file(path, analysis)
            self.analyzer.doc_generator.generate_diagrams(path, analysis)

            console.print(f"[green]✓ Updated:[/] {path.name}")

        except Exception as e:
            console.print(f"[red]Error updating {path.name}: {e}[/]")
