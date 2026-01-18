"""
Diagram generator using Graphviz.

Generates class diagrams with clickable hyperlinks to documentation.
"""

from pathlib import Path
from typing import Optional
import subprocess
import shutil

from autodocgen.config import Config
from autodocgen.parser.models import ClassInfo


class DiagramGenerator:
    """
    Generates class diagrams using Graphviz.

    Diagrams are output as SVG with embedded hyperlinks to documentation.
    """

    def __init__(self, config: Config):
        """
        Initialize the diagram generator.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.output_format = config.documentation.diagram_format
        self._graphviz_available = self._check_graphviz()

    def _check_graphviz(self) -> bool:
        """Check if Graphviz is available."""
        return shutil.which("dot") is not None

    def generate_class_diagram(
        self,
        classes: list[ClassInfo],
        output_path: Path,
        title: Optional[str] = None,
    ) -> bool:
        """
        Generate a class diagram.

        Args:
            classes: List of classes to include
            output_path: Path to save the diagram
            title: Optional diagram title

        Returns:
            True if successful, False otherwise
        """
        if not self._graphviz_available:
            return False

        if not classes:
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate DOT source
        dot_source = self._generate_dot(classes, title)

        # Write to temp file and convert
        dot_path = output_path.with_suffix(".dot")
        dot_path.write_text(dot_source, encoding="utf-8")

        try:
            subprocess.run(
                ["dot", f"-T{self.output_format}", "-o", str(output_path), str(dot_path)],
                check=True,
                capture_output=True,
            )
            dot_path.unlink()  # Clean up DOT file
            return True
        except subprocess.CalledProcessError:
            return False

    def generate_mermaid(
        self,
        classes: list[ClassInfo],
        title: Optional[str] = None,
    ) -> str:
        """Generate Mermaid class diagram source."""
        lines = ["classDiagram"]
        
        # Track all class names for relationship resolution
        class_names = {cls.qualified_name for cls in classes}
        class_names.update({cls.name for cls in classes})
        
        # Generate classes
        for cls in classes:
            safe_name = self._sanitize_id(cls.qualified_name)
            
            # Add class definition
            if cls.kind.value == "struct":
                 lines.append(f"    class {safe_name} {{")
                 lines.append("        <<struct>>")
            else:
                 lines.append(f"    class {safe_name} {{")
            
            # Add methods (limit 10)
            if cls.public_methods:
                for method in cls.public_methods[:10]:
                    prefix = "+" if method.access.value == "public" else "#"
                    # Sanitize method name
                    name = method.name.replace("~", "destroy_").replace("operator=", "operator_assign").replace("operator", "op_")
                    
                    # Sanitize params (remove types just keep names to keep it short, or simplified)
                    params = ", ".join(p.name for p in method.parameters)
                    if len(params) > 20:
                        params = "..."
                        
                    lines.append(f"        {prefix}{name}({params})")
            
            lines.append("    }")
            
        # Relationships
        for cls in classes:
            safe_name = self._sanitize_id(cls.qualified_name)
            
            # Inheritance
            for base in cls.base_classes:
                base_name = self._clean_base_name(base)
                # Find the matched class in the list to get its fully qualified name
                matched_base = next((c for c in classes if c.name == base_name or c.qualified_name.endswith("::" + base_name)), None)
                
                # If found, use its sanitized ID, otherwise check simple name
                if matched_base:
                    base_id = self._sanitize_id(matched_base.qualified_name)
                    lines.append(f"    {base_id} <|-- {safe_name}")
                elif base_name in class_names: # Fallback if specific class not found but name exists
                     # This fallback might be risky if names are ambiguous, but better than nothing
                     # However, since we keyed class_names by qualified and simple names, we need to know which one it is.
                     # If we can't find the object, we can't get the qualified name. 
                     # Let's try to assume it matches one of the qualified names if simplest match works
                     pass 

            # Composition/Aggregation
            for member in cls.members:
                member_type = self._extract_type_name(member.type_spelling)
                
                 # Find the matched class
                matched_member = next((c for c in classes if c.name == member_type or c.qualified_name.endswith("::" + member_type)), None)
                
                if matched_member and matched_member.qualified_name != cls.qualified_name:
                    member_id = self._sanitize_id(matched_member.qualified_name)
                    # Check if pointer/reference for aggregation vs composition
                    is_pointer = "*" in member.type_spelling or "ptr" in member.type_spelling
                    arrow = "o--" if is_pointer else "*--"
                    lines.append(f"    {safe_name} {arrow} {member_id} : {member.name}")

        return "\n".join(lines)

    def _generate_dot(
        self,
        classes: list[ClassInfo],
        title: Optional[str] = None,
    ) -> str:
        """Generate DOT source for a class diagram."""
        lines = [
            "digraph ClassDiagram {",
            '    rankdir=TB;',
            '    node [shape=record, style=filled, fillcolor="#E3F2FD", fontname="Helvetica"];',
            '    edge [fontname="Helvetica", fontsize=10];',
            "",
        ]

        if title:
            lines.append(f'    labelloc="t";')
            lines.append(f'    label="{title}";')
            lines.append("")

        # Track all class names for relationship resolution
        class_names = {cls.qualified_name for cls in classes}
        class_names.update({cls.name for cls in classes})

        # Generate nodes
        for cls in classes:
            node_id = self._sanitize_id(cls.qualified_name)
            label = self._generate_class_label(cls)
            href = self._get_doc_link(cls)

            lines.append(
                f'    {node_id} [label="{label}", '
                f'href="{href}", target="_top", '
                f'fillcolor="{self._get_class_color(cls)}"];'
            )

        lines.append("")

        # Generate relationships
        for cls in classes:
            node_id = self._sanitize_id(cls.qualified_name)

            # Inheritance
            for base in cls.base_classes:
                base_name = self._clean_base_name(base)
                if base_name in class_names:
                    base_id = self._sanitize_id(base_name)
                    lines.append(
                        f'    {node_id} -> {base_id} '
                        f'[arrowhead=empty, style=solid];'
                    )

            # Composition/Aggregation (from member types)
            for member in cls.members:
                member_type = self._extract_type_name(member.type_spelling)
                if member_type in class_names and member_type != cls.name:
                    member_id = self._sanitize_id(member_type)
                    lines.append(
                        f'    {node_id} -> {member_id} '
                        f'[arrowhead=diamond, style=dashed, label="{member.name}"];'
                    )

        lines.append("}")

        return "\n".join(lines)

    def _generate_class_label(self, cls: ClassInfo) -> str:
        """Generate a UML-style label for a class."""
        # Class name section
        stereotype = ""
        if cls.kind.value == "struct":
            stereotype = "«struct»\\n"
        elif cls.template_params:
            stereotype = "«template»\\n"

        parts = [f"{stereotype}{cls.name}"]

        # Methods section (public only, limit to 5)
        if cls.public_methods:
            parts.append("|")
            for method in cls.public_methods[:5]:
                prefix = "+" if method.access.value == "public" else "#"
                params = ", ".join(p.name for p in method.parameters)
                parts.append(f"{prefix}{method.name}({params})\\l")

            if len(cls.public_methods) > 5:
                parts.append(f"... +{len(cls.public_methods) - 5} more\\l")

        return "{" + "".join(parts) + "}"

    def _get_class_color(self, cls: ClassInfo) -> str:
        """Get a color based on class type."""
        if cls.kind.value == "struct":
            return "#E8F5E9"  # Light green
        elif cls.template_params:
            return "#FFF3E0"  # Light orange
        else:
            return "#E3F2FD"  # Light blue

    def _get_doc_link(self, cls: ClassInfo) -> str:
        """Get the documentation link for a class."""
        if cls.location:
            # Link to the file's documentation
            relative = cls.location.file_path.name
            anchor = cls.qualified_name.lower().replace("::", "-")
            return f"../{relative}.md#{anchor}"
        return "#"

    def _sanitize_id(self, name: str) -> str:
        """Sanitize a name for use as a DOT node ID."""
        return name.replace("::", "_").replace("<", "_").replace(">", "_").replace(" ", "_")

    def _clean_base_name(self, base: str) -> str:
        """Clean a base class specification."""
        # Remove access specifiers
        for spec in ["public ", "protected ", "private ", "virtual "]:
            base = base.replace(spec, "")

        # Remove template arguments for matching
        if "<" in base:
            base = base[:base.index("<")]

        return base.strip()

    def _extract_type_name(self, type_spelling: str) -> str:
        """Extract the base type name from a type spelling."""
        # Remove qualifiers
        type_name = type_spelling
        for remove in ["const ", "volatile ", "&", "*", "&&"]:
            type_name = type_name.replace(remove, "")

        # Handle smart pointers
        for wrapper in ["std::unique_ptr", "std::shared_ptr", "sp", "wp"]:
            if type_name.startswith(wrapper + "<"):
                # Extract inner type
                start = type_name.index("<") + 1
                end = type_name.rindex(">")
                type_name = type_name[start:end]
                break

        # Remove remaining template args
        if "<" in type_name:
            type_name = type_name[:type_name.index("<")]

        return type_name.strip()

    def generate_dependency_diagram(
        self,
        file_dependencies: dict[Path, list[Path]],
        output_path: Path,
    ) -> bool:
        """
        Generate a file dependency diagram.

        Args:
            file_dependencies: Mapping of files to their dependencies
            output_path: Path to save the diagram

        Returns:
            True if successful, False otherwise
        """
        if not self._graphviz_available:
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "digraph Dependencies {",
            '    rankdir=LR;',
            '    node [shape=box, style=filled, fillcolor="#ECEFF1", fontname="Helvetica"];',
            "",
        ]

        for file_path, deps in file_dependencies.items():
            file_id = self._sanitize_id(file_path.stem)
            lines.append(f'    {file_id} [label="{file_path.name}"];')

            for dep in deps:
                dep_id = self._sanitize_id(dep.stem)
                lines.append(f'    {file_id} -> {dep_id};')

        lines.append("}")

        dot_source = "\n".join(lines)
        dot_path = output_path.with_suffix(".dot")
        dot_path.write_text(dot_source, encoding="utf-8")

        try:
            subprocess.run(
                ["dot", f"-T{self.output_format}", "-o", str(output_path), str(dot_path)],
                check=True,
                capture_output=True,
            )
            dot_path.unlink()
            return True
        except subprocess.CalledProcessError:
            return False
