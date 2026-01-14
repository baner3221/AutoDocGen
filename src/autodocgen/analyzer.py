"""
Main analyzer that orchestrates the documentation generation pipeline.
"""

from pathlib import Path
from typing import Optional
import fnmatch

from rich.console import Console
from rich.progress import Progress, TaskID

from autodocgen.config import Config
from autodocgen.parser import CppParser, CppFileAnalysis
from autodocgen.chunker import IntelligentChunker, ContextBuilder
from autodocgen.llm import OllamaClient, PromptBuilder
from autodocgen.generator import DocumentationGenerator


console = Console()


class CodebaseAnalyzer:
    """
    Main analyzer that orchestrates the documentation pipeline.

    Workflow:
    1. Scan codebase for C++ files
    2. Parse each file to extract structure
    3. Chunk large files for LLM processing
    4. Generate documentation via LLM
    5. Synthesize and output final documentation
    """

    def __init__(self, config: Config):
        """
        Initialize the codebase analyzer.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.parser = CppParser(config)
        self.chunker = IntelligentChunker(config)
        self.context_builder = ContextBuilder(config)
        self.llm_client = OllamaClient(config)
        self.prompt_builder = PromptBuilder(codebase_type="android")
        self.doc_generator = DocumentationGenerator(config)

        self._files: list[Path] = []
        self._analyses: dict[Path, CppFileAnalysis] = {}

    def scan_codebase(self) -> int:
        """
        Scan the codebase for C++ files.

        Returns:
            Number of C++ files found
        """
        self._files = []
        extensions = set(self.config.parser.supported_extensions)
        exclude_patterns = self.config.parser.exclude_patterns

        for file_path in self.config.codebase_path.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix not in extensions:
                continue

            # Check exclude patterns
            relative = file_path.relative_to(self.config.codebase_path)
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(str(relative), pattern):
                    excluded = True
                    break

            if not excluded:
                self._files.append(file_path)

        return len(self._files)

    def parse_all(
        self, progress: Optional[Progress] = None, task_id: Optional[TaskID] = None
    ) -> None:
        """
        Parse all discovered C++ files.

        Args:
            progress: Optional Rich progress bar
            task_id: Optional TaskID for progress updates
        """
        total = len(self._files)
        
        if progress and task_id is not None:
            progress.update(task_id, total=total)

        for i, file_path in enumerate(self._files):
            if progress:
                # Update description and advance
                desc = f"Parsing {file_path.name}"
                if task_id is not None:
                    progress.update(task_id, description=desc, advance=1)
                else:
                    # Fallback
                    progress.update(progress.task_ids[0], description=desc)

            try:
                analysis = self.parser.parse_file(file_path)
                self._analyses[file_path] = analysis

                # Register for cross-referencing
                self.context_builder.register_analysis(analysis)

            except Exception as e:
                console.print(f"[red]Error parsing {file_path}: {e}[/]")

    def generate_documentation(
        self, progress: Optional[Progress] = None, task_id: Optional[TaskID] = None
    ) -> None:
        """
        Generate documentation for all parsed files.

        Args:
            progress: Optional Rich progress bar
            task_id: Optional TaskID for progress updates
        """
        # Check LLM connection
        llm_available = self.llm_client.check_connection()
        if not llm_available:
            console.print(
                "[yellow]Cannot connect to Ollama. Falling back to structural documentation only.[/]"
            )

        total = len(self._analyses)
        
        if progress and task_id is not None:
            progress.update(task_id, total=total)

        for i, (file_path, analysis) in enumerate(self._analyses.items()):
            if progress:
                desc = f"Documenting {file_path.name}"
                if task_id is not None:
                    progress.update(task_id, description=desc, advance=1)
                else:
                    progress.update(
                        progress.task_ids[0],
                        description=f"Documenting [{i+1}/{total}] {file_path.name}",
                    )

            try:
                if llm_available:
                    self._document_file(file_path, analysis)
                else:
                    # Fallback: Structural docs only
                    doc = self.doc_generator.generate_file_documentation(analysis)
                    analysis.file_documentation = doc
                    self.doc_generator.write_file_documentation(file_path, analysis, doc)
                    
            except Exception as e:
                console.print(f"[red]Error documenting {file_path}: {e}[/]")

    def _document_file(self, file_path: Path, analysis: CppFileAnalysis) -> None:
        """
        Generate documentation for a single file.

        Args:
            file_path: Path to the source file
            analysis: Parsed analysis of the file
        """
        # Read source code
        source_code = file_path.read_text(encoding="utf-8", errors="replace")

        # Chunk the file
        chunks = self.chunker.chunk_file(file_path, analysis, source_code)

        # Enrich chunk contexts
        for chunk in chunks:
            self.context_builder.enrich_chunk_context(chunk, analysis)

        # Process each chunk with LLM
        chunk_docs: list[str] = []
        system_prompt = self.prompt_builder.get_system_prompt()

        for chunk in chunks:
            # Build prompt
            dep_context = self._get_dependency_context(chunk)
            prompt = self.prompt_builder.build_chunk_prompt(chunk, dep_context)

            # Generate documentation
            response = self.llm_client.generate(prompt, system_prompt)

            if response.error:
                console.print(f"[yellow]LLM error for {chunk.primary_symbol}: {response.error}[/]")
                chunk_docs.append(f"# {chunk.primary_symbol}\n\n*Documentation generation failed*")
            else:
                chunk_docs.append(response.content)
                chunk.llm_response = response.content
                chunk.is_processed = True

        # Synthesize if multiple chunks
        if len(chunks) > 1:
            synthesis_prompt = self.prompt_builder.build_synthesis_prompt(
                chunk_docs, str(file_path)
            )
            final_doc = self.llm_client.generate(synthesis_prompt, system_prompt)
            documentation = final_doc.content if not final_doc.error else "\n\n".join(chunk_docs)
        else:
            documentation = chunk_docs[0] if chunk_docs else ""

        # Store documentation in analysis
        analysis.file_documentation = documentation

        # Generate output files
        self.doc_generator.write_file_documentation(file_path, analysis, documentation)

    def _get_dependency_context(self, chunk) -> str:
        """Get cross-reference context for a chunk's dependencies."""
        contexts: list[str] = []

        for dep in chunk.context.dependencies[:5]:  # Limit to avoid huge prompts
            dep_doc = self.context_builder.get_dependency_context(dep)
            if dep_doc:
                contexts.append(f"### {dep}\n\n{dep_doc}")

        return "\n\n".join(contexts) if contexts else ""

    def generate_diagrams(
        self, progress: Optional[Progress] = None, task_id: Optional[TaskID] = None
    ) -> None:
        """
        Generate class diagrams for documented files.

        Args:
            progress: Optional Rich progress bar
            task_id: Optional TaskID for progress updates
        """
        total = len(self._analyses)
        
        if progress and task_id is not None:
            progress.update(task_id, total=total)

        for i, (file_path, analysis) in enumerate(self._analyses.items()):
            if progress:
                desc = f"Diagrams {file_path.name}"
                if task_id is not None:
                    progress.update(task_id, description=desc, advance=1)
                else:
                    progress.update(
                        progress.task_ids[0],
                        description=f"Diagrams [{i+1}/{total}] {file_path.name}",
                    )

            try:
                self.doc_generator.generate_diagrams(file_path, analysis)
            except Exception as e:
                console.print(f"[yellow]Error generating diagrams for {file_path}: {e}[/]")

        # Generate overall class diagram
        self.doc_generator.generate_codebase_diagram(self._analyses)

    def generate_index(self) -> None:
        """Generate the main index page."""
        self.doc_generator.generate_index(self._analyses)

    def close(self) -> None:
        """Clean up resources."""
        self.llm_client.close()
