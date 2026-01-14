"""
Prompt templates for comprehensive C++ documentation generation.

These prompts are designed to generate detailed, cross-referenced documentation
for Android native libraries and Linux kernel drivers.
"""

from typing import Optional
from dataclasses import dataclass

from autodocgen.parser.models import (
    ClassInfo,
    MethodInfo,
    FunctionInfo,
    ParameterInfo,
)
from autodocgen.chunker.models import CodeChunk


# System prompts for different contexts
SYSTEM_PROMPT_ANDROID = """You are an expert C++ documentation generator specializing in Android native services and libraries.

You generate COMPREHENSIVE, DETAILED documentation - NOT brief summaries.

Key principles:
1. Every function gets a full multi-paragraph description
2. Every parameter is explained in detail (purpose, valid values, ownership)
3. Dependencies on other classes are cross-referenced with links
4. Side effects, thread safety, and lifecycle are documented
5. Usage examples are provided for public APIs
6. Mermaid diagrams are used for complex flows

You understand:
- Android Binder IPC mechanisms
- HIDL/AIDL interfaces
- Hardware Abstraction Layer (HAL) patterns
- SurfaceFlinger, AudioFlinger, and other system services
- Native library patterns (sp<>, wp<>, RefBase)

Output format: Markdown with proper headings, code blocks, and tables."""

SYSTEM_PROMPT_KERNEL = """You are an expert documentation generator for Linux kernel code.

You generate COMPREHENSIVE, DETAILED documentation - NOT brief summaries.

Key principles:
1. Every function gets a full multi-paragraph description
2. Every parameter is explained in detail (purpose, valid values, ownership)
3. Locking requirements are always documented
4. Context requirements (interrupt, process, atomic) are specified
5. Error handling paths are documented
6. Memory allocation flags and constraints are noted

You understand:
- Kernel locking primitives (spinlock, mutex, RCU)
- Memory allocation contexts (GFP_KERNEL, GFP_ATOMIC)
- Device driver lifecycle (probe, remove, suspend, resume)
- Interrupt context restrictions
- Kernel coding style and conventions

Output format: Markdown with proper headings, code blocks, and tables."""


@dataclass
class PromptContext:
    """Context for prompt generation."""
    file_path: str
    namespace: str
    parent_class: Optional[str]
    dependency_context: str
    codebase_type: str  # "android" or "kernel"


class PromptBuilder:
    """
    Builds prompts for comprehensive C++ documentation generation.
    """

    def __init__(self, codebase_type: str = "android"):
        """
        Initialize the prompt builder.

        Args:
            codebase_type: Type of codebase ("android" or "kernel")
        """
        self.codebase_type = codebase_type

    def get_system_prompt(self) -> str:
        """Get the appropriate system prompt for the codebase type."""
        if self.codebase_type == "kernel":
            return SYSTEM_PROMPT_KERNEL
        return SYSTEM_PROMPT_ANDROID

    def build_chunk_prompt(
        self,
        chunk: CodeChunk,
        dependency_context: str = "",
    ) -> str:
        """
        Build a prompt for analyzing a code chunk.

        Args:
            chunk: The code chunk to analyze
            dependency_context: Pre-analyzed context for dependencies

        Returns:
            The formatted prompt string
        """
        prompt_parts = [
            "# Documentation Generation Request",
            "",
            "Generate COMPREHENSIVE documentation for the following C++ code.",
            "**DO NOT generate brief summaries. Provide DETAILED, COMPLETE documentation.**",
            "",
            "## File Context",
            f"- **File:** `{chunk.file_path}`",
            f"- **Lines:** {chunk.line_start} - {chunk.line_end}",
            f"- **Chunk:** {chunk.chunk_index + 1} of {chunk.total_chunks}",
        ]

        if chunk.context.namespace:
            prompt_parts.append(f"- **Namespace:** `{chunk.context.namespace}`")

        if chunk.context.parent_class:
            prompt_parts.append(f"- **Parent Class:** `{chunk.context.parent_class}`")
            if chunk.context.parent_class_description:
                prompt_parts.append(f"  - {chunk.context.parent_class_description}")

        # Dependencies
        if chunk.context.dependencies:
            prompt_parts.extend([
                "",
                "## Dependencies Used",
            ])
            for dep in chunk.context.dependencies:
                desc = chunk.context.dependency_descriptions.get(dep, "")
                if desc:
                    prompt_parts.append(f"- **{dep}**: {desc}")
                else:
                    prompt_parts.append(f"- **{dep}**")

        # Dependency context if provided
        if dependency_context:
            prompt_parts.extend([
                "",
                "## Dependency Documentation (for cross-referencing)",
                dependency_context,
            ])

        # The code
        prompt_parts.extend([
            "",
            "## Code to Document",
            "```cpp",
            chunk.code,
            "```",
            "",
        ])

        # Documentation requirements
        prompt_parts.extend(self._get_documentation_requirements(chunk))

        return "\n".join(prompt_parts)

    def build_class_prompt(
        self,
        class_info: ClassInfo,
        code: str,
        dependency_context: str = "",
    ) -> str:
        """
        Build a prompt for documenting a class.

        Args:
            class_info: Parsed class information
            code: The class source code
            dependency_context: Context for dependencies

        Returns:
            The formatted prompt string
        """
        prompt_parts = [
            "# Class Documentation Request",
            "",
            "Generate COMPREHENSIVE documentation for this C++ class.",
            "",
            f"## Class: `{class_info.qualified_name}`",
            "",
        ]

        # Class metadata
        if class_info.template_params:
            prompt_parts.append(f"**Template Parameters:** `<{', '.join(class_info.template_params)}>`")

        if class_info.base_classes:
            prompt_parts.append(f"**Base Classes:** {', '.join(f'`{b}`' for b in class_info.base_classes)}")

        prompt_parts.append(f"**Methods:** {len(class_info.methods)}")
        prompt_parts.append(f"**Members:** {len(class_info.members)}")

        # Method list for overview
        prompt_parts.extend([
            "",
            "### Method Overview",
        ])
        for method in class_info.public_methods[:20]:  # Limit to first 20
            prompt_parts.append(f"- `{method.signature}`")

        if dependency_context:
            prompt_parts.extend([
                "",
                "## Dependency Context",
                dependency_context,
            ])

        prompt_parts.extend([
            "",
            "## Source Code",
            "```cpp",
            code,
            "```",
            "",
        ])

        # Requirements
        prompt_parts.extend([
            "## Required Documentation Sections",
            "",
            "### 1. Class Overview (2-3 paragraphs)",
            "- What is this class responsible for?",
            "- How does it fit into the larger system?",
            "- What design patterns does it implement?",
            "",
            "### 2. Class Diagram",
            "Generate a Mermaid class diagram showing:",
            "- This class",
            "- Base classes",
            "- Key relationships to other classes",
            "",
            "### 3. Constructor/Destructor Documentation",
            "For each constructor:",
            "- When to use this constructor",
            "- Parameter details with ownership semantics",
            "",
            "### 4. Method Documentation",
            "For EACH public method, document:",
            "- Comprehensive description (NOT brief)",
            "- Parameters with purpose, valid values, ownership",
            "- Return value and all possible states",
            "- Side effects and state modifications",
            "- Thread safety considerations",
            "- Usage example if applicable",
            "",
            "### 5. Member Documentation",
            "For each member variable:",
            "- Purpose",
            "- Invariants",
            "- Thread safety",
            "",
            "### 6. Usage Examples",
            "Provide realistic usage examples showing:",
            "- Basic usage",
            "- Common patterns",
            "- Error handling",
        ])

        return "\n".join(prompt_parts)

    def build_function_prompt(
        self,
        func: FunctionInfo,
        code: str,
        dependency_context: str = "",
    ) -> str:
        """
        Build a prompt for documenting a function.

        Args:
            func: Parsed function information
            code: The function source code
            dependency_context: Context for dependencies

        Returns:
            The formatted prompt string
        """
        prompt_parts = [
            "# Function Documentation Request",
            "",
            "Generate COMPREHENSIVE documentation for this C++ function.",
            "",
            f"## Function: `{func.qualified_name}`",
            "",
            f"**Signature:** `{func.signature}`",
            "",
        ]

        if func.template_params:
            prompt_parts.append(f"**Template Parameters:** `<{', '.join(func.template_params)}>`")

        # Parameters overview
        if func.parameters:
            prompt_parts.extend([
                "",
                "### Parameters",
            ])
            for param in func.parameters:
                prompt_parts.append(f"- `{param.type_spelling} {param.name}`")
                if param.default_value:
                    prompt_parts.append(f"  - Default: `{param.default_value}`")

        if dependency_context:
            prompt_parts.extend([
                "",
                "## Dependency Context",
                dependency_context,
            ])

        prompt_parts.extend([
            "",
            "## Source Code",
            "```cpp",
            code,
            "```",
            "",
        ])

        # Requirements
        prompt_parts.extend(self._get_function_doc_requirements())

        return "\n".join(prompt_parts)

    def _get_documentation_requirements(self, chunk: CodeChunk) -> list[str]:
        """Get documentation requirements based on chunk type."""
        if chunk.chunk_type == "class":
            return [
                "## Required Documentation",
                "",
                "Generate the following for ALL classes and methods in this code:",
                "",
                "### For Each Class:",
                "1. **Overview** (2-3 paragraphs): Purpose, design, system integration",
                "2. **Class Diagram** (Mermaid): Inheritance and key relationships",
                "3. **Usage Examples**",
                "",
                "### For Each Method:",
                "1. **Comprehensive Description** (multiple paragraphs)",
                "2. **Parameters**: Purpose, type semantics, valid values, ownership",
                "3. **Return Value**: All possible states, ownership",
                "4. **Side Effects**: State modifications, locks, I/O",
                "5. **Dependencies**: Cross-reference other classes used",
                "6. **Usage Context**: When called, prerequisites",
                "7. **Thread Safety**",
                "",
                "Format as Markdown with cross-reference links: [ClassName::method()](#classname-method)",
            ]
        else:
            return self._get_function_doc_requirements()

    def _get_function_doc_requirements(self) -> list[str]:
        """Get documentation requirements for functions."""
        requirements = [
            "## Required Documentation",
            "",
            "### 1. Comprehensive Description (2-4 paragraphs)",
            "- What does this function do?",
            "- Why does it exist? What problem does it solve?",
            "- How does it fit into the larger workflow?",
            "- Key algorithms or techniques used",
            "",
            "### 2. Parameters (DETAILED for each)",
            "For EACH parameter:",
            "- **Purpose**: Why does this parameter exist?",
            "- **Type Semantics**: What does the type represent?",
            "- **Valid Values**: Acceptable range, constraints",
            "- **Ownership**: Who owns memory? Borrowed or transferred?",
            "- **Nullability**: Can it be null? What happens?",
            "",
            "### 3. Return Value",
            "- What does it represent?",
            "- All possible return states",
            "- Error conditions and how they're indicated",
            "- Ownership of returned objects",
            "",
            "### 4. Dependencies Cross-Reference",
            "For each external class/function used:",
            "- Why it's used",
            "- How it's used in this context",
            "- Link format: [ClassName::method()](#classname-method)",
            "",
            "### 5. Side Effects",
            "- State modifications",
            "- Locks acquired/released",
            "- I/O operations",
            "- Signals/events emitted",
            "",
            "### 6. Usage Context",
            "- When is this called?",
            "- Prerequisites",
            "- Typical callers",
            "",
            "### 7. Related Functions",
            "Table with relationship types",
            "",
            "### 8. Code Example",
            "At least one usage example",
        ]

        # Add kernel-specific requirements
        if self.codebase_type == "kernel":
            requirements.extend([
                "",
                "### 9. Kernel-Specific (if applicable)",
                "- **Locking**: Required locks, acquired locks, ordering",
                "- **Context**: Can be called from interrupt? Sleeping allowed?",
                "- **Memory**: GFP flags, allocation constraints",
                "- **Error Handling**: Cleanup on error paths",
            ])

        return requirements

    def build_synthesis_prompt(
        self,
        chunk_docs: list[str],
        file_path: str,
    ) -> str:
        """
        Build a prompt to synthesize multiple chunk documentations.

        Args:
            chunk_docs: Documentation from individual chunks
            file_path: Path to the file being documented

        Returns:
            Synthesis prompt
        """
        combined_docs = "\n\n---\n\n".join(chunk_docs)

        return f"""# Documentation Synthesis Request

You are given documentation for multiple chunks of a large C++ file.
Synthesize these into a cohesive, unified documentation file.

## File: `{file_path}`

## Chunk Documentation

{combined_docs}

## Synthesis Requirements

1. **File Overview**: Create a unified overview section
2. **Table of Contents**: Generate a navigable TOC
3. **Merge Class Documentation**: Combine related class docs
4. **Cross-Reference Links**: Ensure all internal links work
5. **Deduplicate**: Remove any redundant information
6. **Class Diagram**: Generate a comprehensive file-level diagram
7. **Maintain Detail**: Do NOT summarize - keep all detailed documentation

Output: Single cohesive Markdown document"""
