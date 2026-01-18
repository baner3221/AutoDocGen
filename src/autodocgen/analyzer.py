"""
Main analyzer that orchestrates the documentation generation pipeline.
"""

from pathlib import Path
from typing import Optional
import re
import fnmatch

from rich.console import Console
from rich.progress import Progress, TaskID

from autodocgen.config import Config
from autodocgen.parser import CppParser, CppFileAnalysis
from autodocgen.chunker import IntelligentChunker, ContextBuilder
from autodocgen.llm import OllamaClient, PromptBuilder
from autodocgen.generator import DocumentationGenerator
from autodocgen.graph import DependencyStore, DependencyExtractor, GraphVisualizer


console = Console()


class CodebaseAnalyzer:
    """
    Main analyzer that orchestrates the documentation pipeline.

    Workflow:
    1. Scan codebase for C++ files
    2. Parse each file to extract structure
    3. Build dependency graph (streaming to SQLite)
    4. Chunk large files for LLM processing
    5. Generate documentation via LLM
    6. Synthesize and output final documentation
    """

    def __init__(self, config: Config, skip_graph: bool = False):
        """
        Initialize the codebase analyzer.

        Args:
            config: AutoDocGen configuration
            skip_graph: If True, skip dependency graph extraction
        """
        self.config = config
        self.skip_graph = skip_graph
        self.parser = CppParser(config)
        self.chunker = IntelligentChunker(config)
        self.context_builder = ContextBuilder(config)
        self.llm_client = OllamaClient(config)
        self.prompt_builder = PromptBuilder(codebase_type="android")
        self.doc_generator = DocumentationGenerator(config)

        # Dependency graph components
        graph_db_path = config.output_path / "dependency_graph.db"
        self.dependency_store = DependencyStore(graph_db_path)
        self.dependency_extractor = DependencyExtractor(self.dependency_store)
        self.graph_visualizer = GraphVisualizer(self.dependency_store)

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

                # Extract dependencies (streaming to SQLite)
                if not self.skip_graph:
                    self.dependency_extractor.extract_file(file_path, analysis)

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
                # Show output snippet
                preview = response.content[:100].replace("\n", " ") + "..."
                console.print(f"[dim]Generated for {chunk.primary_symbol}: {preview}[/]")
                chunk.llm_response = response.content
                chunk.is_processed = True

        # Synthesize if multiple chunks
        if len(chunks) > 1:
            # Skip LLM synthesis to avoid token truncation on large files.
            # Concatenate chunks to preserve all details.
            console.print("[dim]Skipping synthesis to preserve detail (multi-chunk file)[/]")
            documentation = "\n\n".join(chunk_docs)
        else:
            documentation = chunk_docs[0] if chunk_docs else ""

        # Store documentation in analysis
        analysis.file_documentation = documentation

        # Validate completeness
        self._verify_documentation(analysis, documentation)

        # Generate output files
        self.doc_generator.write_file_documentation(file_path, analysis, analysis.file_documentation)

    def _verify_documentation(self, analysis: CppFileAnalysis, documentation: str) -> list[str]:
        """
        Verify that all functions in the analysis are present in the documentation.
        Returns a list of missing function names.
        """
        import re
        missing_functions = []
        
        for func in analysis.functions:
            # Robust Check: Look for the function name in a Markdown Header
            pattern = fr"^#+\s+.*{re.escape(func.name)}"
            match = re.search(pattern, documentation, re.MULTILINE | re.IGNORECASE)
            
            if not match:
                missing_functions.append(func.name)
        
        if missing_functions:
            marker = f"\n\n<!-- validation_failed: missing [{', '.join(missing_functions)}] -->"
            console.print(f"[red]Validation failed: Missing documentation for {len(missing_functions)} functions[/]")
            
            # Append marker to documentation if not already present
            if "validation_failed" not in analysis.file_documentation:
                analysis.file_documentation += marker
                
        return missing_functions

    def repair_documentation(self, file_path: Path, analysis: CppFileAnalysis) -> bool:
        """
        Repair documentation for a file by generating missing function docs individually.
        Returns True if repair was successful.
        """
        # Load existing documentation
        existing_doc = self.doc_generator.read_documentation(file_path)
        if not existing_doc:
            console.print(f"[yellow]No existing documentation found for {file_path.name}, skipping repair.[/]")
            return False

        # Identify missing functions
        missing_names = self._verify_documentation(analysis, existing_doc)
        if not missing_names:
            console.print(f"[green]Documentation for {file_path.name} is already complete.[/]")
            return True

        console.print(f"[bold cyan]Repairing {file_path.name}: Generating docs for {len(missing_names)} missing functions...[/]")
        
        new_docs = []
        system_prompt = self.prompt_builder.get_system_prompt()
        
        for func_name in missing_names:
            # Find the function object
            func_info = next((f for f in analysis.functions if f.name == func_name), None)
            if not func_info:
                continue

            # Build a mini-prompt for just this function
            # We include the class context if available
            context_str = f"## Context\nFile: {file_path.name}\n"
            if func_info.qualified_name:
                context_str += f"Function: {func_info.qualified_name}\n"
            
            # Provide existing doc summary as context
            context_str += "\n## Existing Documentation Summary\n"
            context_str += existing_doc[:1000] + "...\n(truncated)"

            prompt = f"""
{context_str}

## Task
Generate documentation for the following SINGLE function which is missing from the file.
Return ONLY the markdown documentation for this function, starting with a level 2 header (##).

```cpp
{func_info.body_code}
```
"""
            # Query LLM
            response = self.llm_client.generate(prompt, system_prompt)
            if not response.error:
                new_docs.append(response.content)
                console.print(f"[green]  + Generated doc for {func_name}[/]")
            else:
                console.print(f"[red]  ! Failed to generate doc for {func_name}: {response.error}[/]")

        if new_docs:
            # Append new docs to the file
            append_content = "\n\n" + "\n\n".join(new_docs)
            
            # Remove the validation failure marker
            fixed_doc = re.sub(r"\n\n<!-- validation_failed:.*?-->", "", existing_doc, flags=re.DOTALL)
            
            # Append
            final_doc = fixed_doc + append_content
            
            # Update analysis and write to disk
            analysis.file_documentation = final_doc
            self.doc_generator.write_file_documentation(file_path, analysis, final_doc)
            
            console.print(f"[bold green]Successfully repaired {file_path.name}![/]")
            return True
        
        return False

    def _document_file_with_context(
        self,
        file_path: Path,
        analysis: CppFileAnalysis,
        additional_context: dict[str, str],
    ) -> None:
        """
        Generate documentation for a single file using additional context.

        Args:
            file_path: Path to the source file
            analysis: Parsed analysis of the file
            additional_context: Dictionary of context from other files
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

        # Build additional context string
        extra_ctx_str = ""
        if additional_context:
            contexts = []
            for name, summary in additional_context.items():
                 contexts.append(f"#### {name}\n{summary}")
            
            if contexts:
                extra_ctx_str = "\n\n### Related Documentation Context\nThe following summaries from related files may act as context:\n\n" + "\n\n".join(contexts)

        for chunk in chunks:
            # Build prompt
            dep_context = self._get_dependency_context(chunk)
            
            # Inject extra context
            full_context = dep_context + extra_ctx_str
            
            prompt = self.prompt_builder.build_chunk_prompt(chunk, full_context)

            # Generate documentation
            response = self.llm_client.generate(prompt, system_prompt)

            if response.error:
                console.print(f"[yellow]LLM error for {chunk.primary_symbol}: {response.error}[/]")
                chunk_docs.append(f"# {chunk.primary_symbol}\n\n*Documentation generation failed*")
            else:
                chunk_docs.append(response.content)
                # Show output snippet
                preview = response.content[:100].replace("\n", " ") + "..."
                console.print(f"[dim]Generated for {chunk.primary_symbol}: {preview}[/]")
                chunk.llm_response = response.content
                chunk.is_processed = True

        # Synthesize if multiple chunks
        if len(chunks) > 1:
            # Skip LLM synthesis to avoid token truncation on large files.
            # Concatenate chunks to preserve all details.
            console.print("[dim]Skipping synthesis to preserve detail (multi-chunk file)[/]")
            documentation = "\n\n".join(chunk_docs)
        else:
            documentation = chunk_docs[0] if chunk_docs else ""

        # Store documentation in analysis
        analysis.file_documentation = documentation

        # Validate completeness
        self._verify_documentation(analysis, documentation)

        # Generate output files
        self.doc_generator.write_file_documentation(file_path, analysis, analysis.file_documentation)

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
