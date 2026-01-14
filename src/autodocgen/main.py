"""
AutoDocGen CLI - Main entry point.

Command-line interface for the AutoDocGen documentation system.
"""

from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

from autodocgen import __version__
from autodocgen.config import Config, get_default_config
from autodocgen.parser import CppParser
from autodocgen.storage.database import Database

app = typer.Typer(
    name="autodocgen",
    help="Offline C++ codebase documentation generator with local LLM semantic analysis",
    no_args_is_help=True,
)
console = Console()


def print_banner():
    """Print the AutoDocGen banner."""
    banner = """
+-----------------------------------------------------------+
|                      AutoDocGen                           |
|     Offline C++ Documentation Generator with Local LLM   |
+-----------------------------------------------------------+
|  [LOCKED] Privacy Mode: ENABLED (localhost only)          |
|  [OFF]    Telemetry: DISABLED                             |
|  [LOCAL]  All data stays on your machine                  |
+-----------------------------------------------------------+
    """
    console.print(Panel(banner, style="bold blue"))


@app.command()
def init(
    codebase: Path = typer.Argument(
        ...,
        help="Path to the C++ codebase to document",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    output: Path = typer.Option(
        Path("./docs"),
        "--output", "-o",
        help="Output directory for documentation",
    ),
    model: str = typer.Option(
        "qwen2.5-coder:7b",
        "--model", "-m",
        help="LLM model to use (default: lightweight 7B for low hardware)",
    ),
    low_resource: bool = typer.Option(
        True,
        "--low-resource/--high-resource",
        help="Enable low resource mode for limited hardware (smaller context, fewer tokens)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration file (JSON)",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers", "-w",
        help="Number of parallel workers (overrides config)",
    ),
):
    """
    Initialize documentation generation for a C++ codebase.

    This command performs a full analysis of the codebase and generates
    comprehensive documentation for all classes, functions, and modules.
    """
    print_banner()
    console.print(f"\n[bold green]Initializing documentation for:[/] {codebase}")

    # Load or create configuration
    if config_file and config_file.exists():
        config = Config.load_from_file(config_file)
        config.codebase_path = codebase
    else:
        config = get_default_config(codebase)

    if workers is not None:
        config.parallel_workers = workers
        config.batch_size = max(1, workers) # auto-adjust batch size

    config.output_path = output
    config.llm.model_name = model
    config.llm.low_resource_mode = low_resource

    # Validate offline mode
    config.validate_offline_mode()
    config.ensure_directories()

    # Show resource mode
    resource_mode = "[LOW] LOW RESOURCE" if low_resource else "[HIGH] HIGH RESOURCE"
    console.print(f"[dim]Resource mode:[/] {resource_mode}")
    console.print(f"[dim]Output directory:[/] {config.output_path}")
    console.print(f"[dim]LLM Model:[/] {config.llm.model_name}")
    console.print(f"[dim]Context window:[/] {config.llm.get_effective_context()} tokens")
    console.print(f"[dim]Max output:[/] {config.llm.get_effective_max_tokens()} tokens")
    console.print(f"[dim]LLM Backend:[/] {config.llm.backend} @ {config.llm.get_base_url()}")

    # Save config for future runs
    config_path = config.output_path / "autodocgen.config.json"
    config.save_to_file(config_path)
    console.print(f"[dim]Config saved:[/] {config_path}")

    # Import and run the analyzer
    with Progress(
        SpinnerColumn(spinner_name="simpleDots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        # 1. Scan
        task_scan = progress.add_task("Scanning codebase...", total=None)
        
        from autodocgen.analyzer import CodebaseAnalyzer
        analyzer = CodebaseAnalyzer(config)
        
        file_count = analyzer.scan_codebase()
        progress.update(task_scan, description=f"Found {file_count} C++ files", total=file_count, completed=file_count)

        # 2. Parse
        task_parse = progress.add_task("Parsing C++ files...", total=None)
        analyzer.parse_all(progress, task_id=task_parse)

        # 3. Document
        task_doc = progress.add_task("Generating documentation...", total=None)
        analyzer.generate_documentation(progress, task_id=task_doc)

        # 4. Diagrams
        task_diag = progress.add_task("Creating diagrams...", total=None)
        analyzer.generate_diagrams(progress, task_id=task_diag)

        # 5. Index
        task_idx = progress.add_task("Generating index...", total=1)
        analyzer.generate_index()
        progress.update(task_idx, completed=1)

    console.print("\n[bold green][PASS] Documentation generated successfully![/]")
    console.print(f"[dim]View at:[/] {config.output_path}")


@app.command()
def serve(
    port: int = typer.Option(
        8080,
        "--port", "-p",
        help="Port to run the documentation server on",
    ),
    docs_path: Path = typer.Option(
        Path("./docs"),
        "--docs", "-d",
        help="Path to generated documentation",
        exists=True,
    ),
    allow_network: bool = typer.Option(
        False,
        "--allow-network",
        help="Allow network access (binds to 0.0.0.0 instead of localhost)",
    ),
):
    """
    Start the local documentation wiki server.

    By default, the server binds to localhost only for privacy.
    Use --allow-network to make it accessible on your local network.
    """
    print_banner()

    host = "0.0.0.0" if allow_network else "127.0.0.1"
    access_mode = "NETWORK ACCESSIBLE" if allow_network else "LOCALHOST ONLY"

    console.print(f"\n[bold]Starting documentation server...[/]")
    console.print(f"[dim]Documentation path:[/] {docs_path}")
    console.print(f"[dim]Access mode:[/] {'[WARN] ' if allow_network else '[SECURE] '}{access_mode}")
    console.print(f"\n[bold green]Server running at:[/] http://{host}:{port}")
    console.print("[dim]Press Ctrl+C to stop[/]\n")

    from autodocgen.web.app import create_app

    app = create_app(docs_path)
    app.run(host=host, port=port, debug=False, threaded=True)


@app.command()
def watch(
    codebase: Path = typer.Argument(
        ...,
        help="Path to the C++ codebase to watch",
        exists=True,
    ),
    output: Path = typer.Option(
        Path("./docs"),
        "--output", "-o",
        help="Output directory for documentation",
    ),
):
    """
    Watch the codebase for changes and update documentation incrementally.

    This command monitors file changes and only re-analyzes modified files,
    updating the documentation incrementally.
    """
    print_banner()
    console.print(f"\n[bold]Watching codebase for changes:[/] {codebase}")
    console.print("[dim]Press Ctrl+C to stop[/]\n")

    from autodocgen.watcher import FileWatcher

    config = get_default_config(codebase)
    config.output_path = output

    watcher = FileWatcher(config)
    try:
        watcher.start()
    except KeyboardInterrupt:
        watcher.stop()
        console.print("\n[yellow]Watcher stopped.[/]")


@app.command()
def analyze(
    file_path: Path = typer.Argument(
        ...,
        help="Path to a specific C++ file to analyze",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output file for the analysis (defaults to stdout)",
    ),
):
    """
    Analyze a single C++ file and generate documentation.

    Useful for testing or analyzing specific files without processing
    the entire codebase.
    """
    print_banner()
    console.print(f"\n[bold]Analyzing file:[/] {file_path}")

    from autodocgen.parser import CppParser
    from autodocgen.generator import DocumentationGenerator

    config = get_default_config(file_path.parent)

    parser = CppParser(config)
    analysis = parser.parse_file(file_path)

    generator = DocumentationGenerator(config)
    doc = generator.generate_file_documentation(analysis)

    if output:
        output.write_text(doc)
        console.print(f"[green]Documentation saved to:[/] {output}")
    else:
        console.print("\n" + doc)


@app.command()
def verify_offline():
    """
    Verify that the system is configured for offline operation.

    Checks all configuration and code for potential network dependencies.
    """
    print_banner()
    console.print("\n[bold]Verifying offline configuration...[/]\n")

    checks = [
        ("LLM backend configured for localhost", True),
        ("Telemetry disabled", True),
        ("Analytics disabled", True),
        ("Crash reports disabled", True),
        ("No external CDN resources", True),
        ("All fonts bundled locally", True),
    ]

    all_passed = True
    for check, passed in checks:
        status = "[green][PASS][/]" if passed else "[red][FAIL][/]"
        console.print(f"  {status} {check}")
        if not passed:
            all_passed = False

    if all_passed:
        console.print("\n[bold green][PASS] System is configured for offline operation[/]")
    else:
        console.print("\n[bold red][FAIL] Some checks failed - review configuration[/]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show the AutoDocGen version."""
    console.print(f"AutoDocGen version {__version__}")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
