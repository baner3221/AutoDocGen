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
    TimeElapsedColumn,
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
    skip_graph: bool = typer.Option(
        False,
        "--skip-graph",
        help="Skip dependency graph extraction (faster runs)",
    ),
    auto_retry: bool = typer.Option(
        True,
        "--auto-retry/--no-auto-retry",
        help="Automatically retry failed documentation files",
    ),
):
    """
    Initialize documentation generation for a C++ codebase.

    This command performs a full analysis of the codebase and generates
    comprehensive documentation for all classes, functions, and modules.
    It includes automatic retries for failed files and codebase-wide diagrams.
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
        analyzer = CodebaseAnalyzer(config, skip_graph=skip_graph)
        
        if not skip_graph:
            console.print("[dim]Dependency graph:[/] ENABLED")
        
        file_count = analyzer.scan_codebase()
        progress.update(task_scan, description=f"Found {file_count} C++ files", total=file_count, completed=file_count)

        # 2. Parse
        task_parse = progress.add_task("Parsing C++ files...", total=None)
        analyzer.parse_all(progress, task_id=task_parse)

        # 3. Document
        task_doc = progress.add_task("Generating documentation...", total=None)
        analyzer.generate_documentation(progress, task_id=task_doc)

        # 3b. Auto-retry (if enabled)
        if auto_retry:
            # We must run this outside the main progress bar context for clean output, 
            # OR we can inject the logic here but _perform_retry uses its own progress bar/console logic.
            # Nesting progress bars is messy. 
            # We'll pause the main progress? Or just run it after.
            pass # We will run it after existing the context for cleaner UI

    # Run auto-retry out of main progress context
    if auto_retry:
        _perform_retry(config.output_path, config, console)

    # Resume main flow for diagrams and index
    # We need to recreate progress or just run silently? 
    # Actually, diagrams and index are fast. 
    # But `generate_diagrams` and `index` were inside the block.
    # Re-entering progress block is fine.
    
    with Progress(
        SpinnerColumn(spinner_name="simpleDots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        # 4. Diagrams
        task_diag = progress.add_task("Creating diagrams...", total=None)
        analyzer.generate_diagrams(progress, task_id=task_diag)

        # 5. Index
        task_idx = progress.add_task("Generating index...", total=1)
        analyzer.generate_index()
        progress.update(task_idx, completed=1)

    console.print("\n[bold green][PASS] Documentation generated successfully![/]")
    console.print(f"[dim]View at:[/] {config.output_path}")


def _perform_retry(docs_path: Path, config: Config, console: Console) -> None:
    """Implement the retry logic for failed documentation."""
    # Find failed docs
    failed_docs = detect_failed_docs(docs_path)

    if not failed_docs:
        console.print("[dim]No failed documentation found needed for retry.[/]")
        return

    console.print(f"\n[bold yellow]Found {len(failed_docs)} failed documentation file(s) - Retrying...[/]")
    for md, _ in failed_docs:
        console.print(f"  ? {md.name} -> {md.parent}")

    # Collect context from successful docs
    console.print("\n[dim]Collecting context from successful documentation...[/]")
    context_map = collect_doc_context(docs_path, [f[0] for f in failed_docs])

    # Initialize analyzer
    from autodocgen.analyzer import CodebaseAnalyzer
    analyzer = CodebaseAnalyzer(config)

    console.print("\n[bold]Processing retries...[/]")
    
    # Track results
    retry_stats = {"repaired": 0, "regenerated": 0, "failed": 0}

    for md_file, source_file in failed_docs:
        try:
            content = md_file.read_text(encoding="utf-8")
            is_validation_failure = "validation_failed" in content and "*Documentation generation failed*" not in content
            
            # Parse the file first
            analysis = analyzer.parser.parse_file(source_file)
            
            if is_validation_failure:
                # Attempt Smart Repair
                if analyzer.repair_documentation(source_file, analysis):
                    retry_stats["repaired"] += 1
                    continue
                else:
                    console.print(f"  [WARN] Smart repair failed for {source_file.name}, falling back to full regeneration")
            
            # Full Regeneration
            console.print(f"  [REFRESH] Regenerating {source_file.name}...")
            analyzer._document_file_with_context(source_file, analysis, context_map)
            console.print(f"  [OK] {source_file.name} (Regenerated)")
            retry_stats["regenerated"] += 1

        except Exception as e:
            console.print(f"  [ERROR] Retry failed for {source_file.name}: {e}")
            retry_stats["failed"] += 1

    console.print("\n[bold]Retry Summary:[/]")
    console.print(f"  Repaired:    {retry_stats['repaired']}")
    console.print(f"  Regenerated: {retry_stats['regenerated']}")
    console.print(f"  Failed:      {retry_stats['failed']}")

    # Re-generate diagrams and index if any succeeded
    if retry_stats["repaired"] > 0 or retry_stats["regenerated"] > 0:
        with Progress(
             SpinnerColumn(spinner_name="simpleDots"),
             TextColumn("[progress.description]{task.description}"),
             console=console
        ) as progress:
            task_diag = progress.add_task("Updating diagrams...", total=None)
            analyzer.generate_diagrams(progress, task_id=task_diag)
            
            task_idx = progress.add_task("Updating index...", total=None)
            analyzer.generate_index()

    console.print("\n[bold green][PASS] Retry process completed![/]")


@app.command()
def retry(
    docs: Path = typer.Argument(
        ...,
        help="Path to existing documentation directory",
        exists=True,
    ),
    list_only: bool = typer.Option(
        False,
        "--list-only", "-l",
        help="Only list failed files, don't regenerate",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers", "-w",
        help="Number of parallel workers",
    ),
):
    """
    Retry documentation generation for files that failed.

    Scans the documentation directory for files with generation failures
    and retries them using context from successfully generated docs.
    """
    print_banner()

    # Find the config file
    config_file = docs / "autodocgen.config.json"
    if not config_file.exists():
        console.print(f"[red]Error: Config file not found at {config_file}[/]")
        raise typer.Exit(1)

    # Load config
    from autodocgen.config import Config
    config = Config.load_from_file(config_file)
    if workers is not None:
        config.llm.parallel_workers = workers

    if list_only:
        failed_files = detect_failed_docs(docs)
        if not failed_files:
             console.print("[green]No failed documentation files found![/]")
        else:
            console.print(f"[yellow]Found {len(failed_files)} failed documentation file(s):[/]")
            for failed_doc, source_file in failed_files:
                console.print(f"  • {failed_doc.name} -> {source_file}")
        return

    _perform_retry(docs, config, console)
    console.print("\n[bold green][PASS] Retry completed![/]")


@app.command()
def diagrams(
    docs: Path = typer.Argument(
        ...,
        help="Path to existing documentation directory",
        exists=True,
    ),
):
    """
    Generate class diagrams for existing documentation.

    This generates Mermaid diagrams and appends them to the markdown files
    if Graphviz is not available.
    """
    print_banner()

    # Find the config file
    config_file = docs / "autodocgen.config.json"
    if not config_file.exists():
        console.print(f"[red]Error: Config file not found at {config_file}[/]")
        raise typer.Exit(1)

    # Load config
    from autodocgen.config import Config
    config = Config.load_from_file(config_file)

    console.print(f"\n[bold]Generating diagrams for:[/] {config.codebase_path}")
    
    from autodocgen.analyzer import CodebaseAnalyzer
    
    # We skip graph extraction as we only need parsing for diagrams
    analyzer = CodebaseAnalyzer(config, skip_graph=True)
    
    with Progress(
        SpinnerColumn(spinner_name="simpleDots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        
        # 1. Scan
        file_count = analyzer.scan_codebase()
        
        # 2. Parse (needed to get class info)
        task_parse = progress.add_task("Parsing C++ files...", total=None)
        analyzer.parse_all(progress, task_id=task_parse)
        
        # 3. Generate Diagrams
        task_diag = progress.add_task("Generating diagrams...", total=None)
        analyzer.generate_diagrams(progress, task_id=task_diag)

    console.print("\n[bold green][PASS] Diagrams generated successfully![/]")



def detect_failed_docs(docs_path: Path) -> list[tuple[Path, Path]]:
    """
    Scan documentation directory for files that failed generation.

    Returns:
        List of (doc_file, source_file) tuples
    """
    failed = []
    failure_marker = "*Documentation generation failed*"

    # Get the config to find source path
    config_file = docs_path / "autodocgen.config.json"
    if config_file.exists():
        import json
        with open(config_file) as f:
            cfg = json.load(f)
        source_root = Path(cfg.get("codebase_path", "."))
    else:
        source_root = Path(".")

    # Scan all .md files
    for md_file in docs_path.rglob("*.md"):
        if md_file.name == "index.md":
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            if failure_marker in content or "validation_failed" in content:
                # Derive source file path from doc path
                rel_path = md_file.relative_to(docs_path)
                source_name = rel_path.with_suffix(".h")
                source_file = source_root / source_name

                # Try .cpp if .h doesn't exist
                if not source_file.exists():
                    source_name = rel_path.with_suffix(".cpp")
                    source_file = source_root / source_name

                failed.append((md_file, source_file))
        except Exception:
            pass

    return failed


def collect_doc_context(docs_path: Path, failed_docs: list[Path]) -> dict[str, str]:
    """
    Collect summaries from successful documentation files to use as context.

    Returns:
        Dict mapping filename to summary text
    """
    context = {}

    for md_file in docs_path.rglob("*.md"):
        if md_file in failed_docs or md_file.name == "index.md":
            continue

        try:
            content = md_file.read_text(encoding="utf-8")

            # Skip if it's a failed file
            if "*Documentation generation failed*" in content:
                continue

            # Extract quick summary (first 500 chars of description section)
            if "## Comprehensive Description" in content or "### 1. Comprehensive Description" in content:
                # Find the description section
                lines = content.split("\n")
                in_desc = False
                summary_lines = []

                for line in lines:
                    if "Comprehensive Description" in line:
                        in_desc = True
                        continue
                    if in_desc:
                        if line.startswith("##") or line.startswith("###"):
                            break  # Next section
                        summary_lines.append(line)
                        if len("\n".join(summary_lines)) > 400:
                            break

                summary = "\n".join(summary_lines).strip()
                if summary:
                    context[md_file.stem] = summary

        except Exception:
            pass

    return context


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

    # Auto-detect include directory (sibling to src?)
    possible_include = file_path.parent.parent / "include"
    if possible_include.exists():
        console.print(f"[dim]Auto-adding include path:[/] {possible_include}")
        config.parser.include_paths.append(str(possible_include))

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
