"""
Documentation generator for Markdown output.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from autodocgen.config import Config
from autodocgen.parser.models import CppFileAnalysis, ClassInfo, MethodInfo, FunctionInfo
from autodocgen.generator.diagram_generator import DiagramGenerator


class DocumentationGenerator:
    """
    Generates Markdown documentation files from analyzed code.
    """

    def __init__(self, config: Config):
        """
        Initialize the documentation generator.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.output_path = config.output_path
        self.diagram_generator = DiagramGenerator(config)

    def write_file_documentation(
        self,
        file_path: Path,
        analysis: CppFileAnalysis,
        documentation: str,
    ) -> Path:
        """
        Write documentation for a file.

        Args:
            file_path: Original source file path
            analysis: Parsed analysis
            documentation: LLM-generated documentation

        Returns:
            Path to the generated documentation file
        """
        # Create output path mirroring source structure
        relative = file_path.relative_to(self.config.codebase_path)
        doc_path = self.output_path / relative.with_suffix(".md")
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate header
        header = self._generate_header(file_path, analysis)

        # Write documentation
        content = f"{header}\n\n{documentation}"
        doc_path.write_text(content, encoding="utf-8")

        return doc_path

    def _generate_header(self, file_path: Path, analysis: CppFileAnalysis) -> str:
        """Generate the documentation header."""
        relative = file_path.relative_to(self.config.codebase_path)

        lines = [
            f"# {file_path.name}",
            "",
            "---",
            "",
            "| Property | Value |",
            "|----------|-------|",
            f"| **Location** | `{relative}` |",
            f"| **Lines** | {analysis.line_count} |",
            f"| **Classes** | {len(analysis.all_classes)} |",
            f"| **Functions** | {len(analysis.all_functions)} |",
            f"| **Last Updated** | {datetime.now().strftime('%Y-%m-%d %H:%M')} |",
            "",
            "---",
        ]

        # Add navigation
        if analysis.all_classes or analysis.all_functions:
            lines.extend([
                "",
                "## Quick Navigation",
                "",
            ])

            if analysis.all_classes:
                lines.append("### Classes")
                for cls in analysis.all_classes:
                    anchor = cls.qualified_name.lower().replace("::", "-")
                    lines.append(f"- [{cls.qualified_name}](#{anchor})")
                lines.append("")

            if analysis.all_functions:
                lines.append("### Functions")
                for func in analysis.all_functions[:20]:  # Limit for readability
                    anchor = func.qualified_name.lower().replace("::", "-")
                    lines.append(f"- [{func.qualified_name}](#{anchor})")

                if len(analysis.all_functions) > 20:
                    lines.append(f"- *... and {len(analysis.all_functions) - 20} more*")

                lines.append("")

            lines.append("---")

        return "\n".join(lines)

    def generate_file_documentation(self, analysis: CppFileAnalysis) -> str:
        """
        Generate documentation for a file (without LLM).

        This creates a basic structure-based documentation.
        Used as fallback when LLM is unavailable.

        Args:
            analysis: Parsed file analysis

        Returns:
            Markdown documentation string
        """
        lines = []

        # Overview
        if analysis.namespaces:
            ns_names = [ns.qualified_name for ns in analysis.namespaces]
            lines.append(f"**Namespaces:** {', '.join(ns_names)}")
            lines.append("")

        # Includes
        if analysis.includes:
            lines.extend([
                "## Includes",
                "",
            ])
            for inc in analysis.includes[:10]:
                icon = "(sys)" if inc.is_system else "(local)"
                lines.append(f"- {icon} `{inc.path}`")

            if len(analysis.includes) > 10:
                lines.append(f"- *... and {len(analysis.includes) - 10} more*")

            lines.append("")

        # Classes
        for cls in analysis.all_classes:
            lines.extend(self._document_class_structure(cls))
            lines.append("")

        # Functions
        if analysis.all_functions:
            lines.extend([
                "## Free Functions",
                "",
            ])
            for func in analysis.all_functions:
                lines.extend(self._document_function_structure(func))
                lines.append("")

        return "\n".join(lines)

    def _document_class_structure(self, cls: ClassInfo) -> list[str]:
        """Generate structural documentation for a class."""
        lines = [
            f"## Class: `{cls.qualified_name}`",
            "",
        ]

        # Class type
        kind = "struct" if cls.kind.value == "struct" else "class"
        lines.append(f"**Type:** {kind}")

        # Base classes
        if cls.base_classes:
            bases = ", ".join(f"`{b}`" for b in cls.base_classes)
            lines.append(f"**Inherits:** {bases}")

        # Template
        if cls.template_params:
            params = ", ".join(cls.template_params)
            lines.append(f"**Template:** `<{params}>`")

        # Location
        if cls.location:
            lines.append(f"**Lines:** {cls.location.to_range_string()}")

        lines.append("")

        # Methods by access
        for access, methods in [
            ("Public", cls.public_methods),
            ("Protected", cls.protected_methods),
            ("Private", cls.private_methods),
        ]:
            if methods:
                lines.extend([
                    f"### {access} Methods",
                    "",
                ])
                for method in methods:
                    sig = f"`{method.signature}`"
                    if method.brief_description:
                        lines.append(f"- {sig} - {method.brief_description}")
                    else:
                        lines.append(f"- {sig}")
                lines.append("")

        # Members
        if cls.members:
            lines.extend([
                "### Members",
                "",
            ])
            for member in cls.members:
                lines.append(f"- `{member.type_spelling} {member.name}`")
            lines.append("")

        return lines

    def _document_function_structure(self, func: FunctionInfo) -> list[str]:
        """Generate structural documentation for a function."""
        lines = [
            f"### `{func.qualified_name}`",
            "",
            f"**Signature:** `{func.signature}`",
            "",
        ]

        if func.location:
            lines.append(f"**Lines:** {func.location.to_range_string()}")
            lines.append("")

        if func.brief_description:
            lines.append(func.brief_description)
            lines.append("")

        if func.parameters:
            lines.extend([
                "**Parameters:**",
                "",
            ])
            for param in func.parameters:
                default = f" = {param.default_value}" if param.default_value else ""
                lines.append(f"- `{param.type_spelling} {param.name}`{default}")
            lines.append("")

        return lines

    def generate_diagrams(self, file_path: Path, analysis: CppFileAnalysis) -> None:
        """
        Generate diagrams for a file.

        Args:
            file_path: Source file path
            analysis: Parsed analysis
        """
        if not self.config.documentation.generate_diagrams:
            return

        if not analysis.all_classes:
            return

        # Generate class diagram
        relative = file_path.relative_to(self.config.codebase_path)
        diagram_path = self.output_path / "diagrams" / relative.with_suffix(".svg")

        # Try generating SVG (requires Graphviz)
        svg_generated = self.diagram_generator.generate_class_diagram(
            analysis.all_classes,
            diagram_path,
        )

        # If SVG failed (e.g. no dot), append Mermaid to markdown
        # If SVG failed (e.g. no dot), append Mermaid to markdown
        if not svg_generated:
            # User requested to NOT display per-file diagrams in the markdown files
            # So we skip appending here. 
            pass 
            # mermaid_source = self.diagram_generator.generate_mermaid(
            #     analysis.all_classes,
            # )
            # 
            # # Append to module doc
            # doc_path = self.output_path / relative.with_suffix(".md")
            # if doc_path.exists():
            #     content = doc_path.read_text(encoding="utf-8")
            #     if "## Class Diagram" not in content:
            #         content += "\n\n## Class Diagram\n\n```mermaid\n" + mermaid_source + "\n```\n"
            #         doc_path.write_text(content, encoding="utf-8")


    def generate_codebase_diagram(
        self,
        analyses: dict[Path, CppFileAnalysis],
    ) -> None:
        """
        Generate an overall codebase class diagram.

        Args:
            analyses: All file analyses
        """
        if not self.config.documentation.generate_diagrams:
            return

        # Aggregate all classes
        all_classes = []
        for analysis in analyses.values():
            all_classes.extend(analysis.all_classes)

        if not all_classes:
            return
            
        diagrams_dir = self.output_path / "diagrams"
        diagrams_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Try Graphviz SVG
        svg_path = diagrams_dir / "codebase_overview.svg"
        svg_generated = self.diagram_generator.generate_class_diagram(
            all_classes,
            svg_path,
            title="Codebase Overview"
        )
        
        # 2. Generate Mermaid Markdown (always generate this for the web view fallback)
        mermaid_path = diagrams_dir / "codebase_overview.md"
        mermaid_source = self.diagram_generator.generate_mermaid(
            all_classes,
            title="Codebase Overview"
        )
        
        # Wrap in HTML div for direct rendering
        content = f"# Codebase Overview\n\n<div class=\"mermaid\">\n{mermaid_source}\n</div>\n"
        mermaid_path.write_text(content, encoding="utf-8")

    def generate_index(self, analyses: dict[Path, CppFileAnalysis]) -> Path:
        """
        Generate the main index page.

        Args:
            analyses: All file analyses

        Returns:
            Path to the generated index file
        """
        lines = [
            "# AutoDocGen Documentation",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
            "## Files",
            "",
        ]

        # Group by directory
        by_dir: dict[str, list[tuple[Path, CppFileAnalysis]]] = {}

        for file_path, analysis in analyses.items():
            relative = file_path.relative_to(self.config.codebase_path)
            dir_name = str(relative.parent)

            if dir_name not in by_dir:
                by_dir[dir_name] = []
            by_dir[dir_name].append((file_path, analysis))

        # Generate tree
        for dir_name, files in sorted(by_dir.items()):
            lines.append(f"### Dir: {dir_name}")
            lines.append("")

            for file_path, analysis in sorted(files, key=lambda x: x[0].name):
                relative = file_path.relative_to(self.config.codebase_path)
                doc_path = relative.with_suffix(".md")
                class_count = len(analysis.all_classes)
                func_count = len(analysis.all_functions)

                lines.append(
                    f"- [{file_path.name}]({doc_path}) "
                    f"({class_count} classes, {func_count} functions)"
                )

            lines.append("")

        # Diagrams section
        lines.extend([
            "---",
            "",
            "## Diagrams",
            "",
            "- [Codebase Overview](diagrams/codebase_overview.svg)",
            "",
        ])

        index_path = self.output_path / "index.md"
        index_path.write_text("\n".join(lines), encoding="utf-8")

        return index_path
