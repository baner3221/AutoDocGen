"""
Data models for C++ code structure representation.

These models capture the semantic structure of C++ code extracted by libclang,
including classes, functions, namespaces, and their relationships.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class AccessSpecifier(str, Enum):
    """C++ access specifier."""
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    NONE = ""  # For free functions


class SymbolKind(str, Enum):
    """Kind of C++ symbol."""
    CLASS = "class"
    STRUCT = "struct"
    UNION = "union"
    ENUM = "enum"
    ENUM_CLASS = "enum_class"
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    DESTRUCTOR = "destructor"
    NAMESPACE = "namespace"
    TYPEDEF = "typedef"
    USING = "using"
    VARIABLE = "variable"
    FIELD = "field"
    MACRO = "macro"
    TEMPLATE = "template"


@dataclass
class SourceLocation:
    """Location in source code."""
    file_path: Path
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0

    def to_range_string(self) -> str:
        """Get a string representation of the line range."""
        if self.line_start == self.line_end:
            return f"L{self.line_start}"
        return f"L{self.line_start}-L{self.line_end}"


@dataclass
class ParameterInfo:
    """Information about a function/method parameter."""
    name: str
    type_name: str
    type_spelling: str  # Full type with qualifiers
    is_const: bool = False
    is_reference: bool = False
    is_pointer: bool = False
    is_rvalue_ref: bool = False
    default_value: Optional[str] = None
    description: str = ""  # LLM-generated description

    @property
    def ownership_hint(self) -> str:
        """Get ownership semantics hint based on type."""
        if "unique_ptr" in self.type_spelling:
            return "exclusive_ownership"
        if "shared_ptr" in self.type_spelling:
            return "shared_ownership"
        if "weak_ptr" in self.type_spelling:
            return "non_owning"
        if self.is_pointer and not self.is_const:
            return "possibly_owning"
        if self.is_reference and not self.is_const:
            return "output_param"
        if self.is_const and (self.is_reference or self.is_pointer):
            return "borrowed"
        return "value"


@dataclass
class MemberInfo:
    """Information about a class/struct member variable."""
    name: str
    type_name: str
    type_spelling: str
    access: AccessSpecifier
    is_static: bool = False
    is_const: bool = False
    is_mutable: bool = False
    default_value: Optional[str] = None
    location: Optional[SourceLocation] = None
    description: str = ""  # LLM-generated description

    @property
    def qualified_name(self) -> str:
        """Get qualified name for documentation linking."""
        return self.name


@dataclass
class MethodInfo:
    """Information about a class method."""
    name: str
    return_type: str
    return_type_spelling: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    access: AccessSpecifier = AccessSpecifier.PUBLIC
    is_virtual: bool = False
    is_pure_virtual: bool = False
    is_override: bool = False
    is_final: bool = False
    is_static: bool = False
    is_const: bool = False
    is_noexcept: bool = False
    is_constructor: bool = False
    is_destructor: bool = False
    is_deleted: bool = False
    is_defaulted: bool = False
    template_params: list[str] = field(default_factory=list)
    location: Optional[SourceLocation] = None
    body_code: str = ""  # The actual method body code
    brief_description: str = ""  # Existing doxygen comment if any
    documentation: str = ""  # LLM-generated comprehensive documentation

    @property
    def signature(self) -> str:
        """Get the method signature string."""
        parts = []
        if self.is_static:
            parts.append("static")
        if self.is_virtual:
            parts.append("virtual")

        params_str = ", ".join(
            f"{p.type_spelling} {p.name}" for p in self.parameters
        )
        parts.append(f"{self.return_type_spelling} {self.name}({params_str})")

        if self.is_const:
            parts.append("const")
        if self.is_noexcept:
            parts.append("noexcept")
        if self.is_override:
            parts.append("override")
        if self.is_final:
            parts.append("final")
        if self.is_pure_virtual:
            parts.append("= 0")

        return " ".join(parts)

    @property
    def qualified_name(self) -> str:
        """Get qualified name for documentation linking."""
        return self.name


@dataclass
class FunctionInfo:
    """Information about a free (non-member) function."""
    name: str
    qualified_name: str  # namespace::function_name
    return_type: str
    return_type_spelling: str
    parameters: list[ParameterInfo] = field(default_factory=list)
    namespace: str = ""
    is_static: bool = False
    is_inline: bool = False
    is_noexcept: bool = False
    is_constexpr: bool = False
    template_params: list[str] = field(default_factory=list)
    location: Optional[SourceLocation] = None
    body_code: str = ""
    brief_description: str = ""
    documentation: str = ""  # LLM-generated comprehensive documentation

    @property
    def signature(self) -> str:
        """Get the function signature string."""
        parts = []
        if self.is_static:
            parts.append("static")
        if self.is_inline:
            parts.append("inline")
        if self.is_constexpr:
            parts.append("constexpr")

        params_str = ", ".join(
            f"{p.type_spelling} {p.name}" for p in self.parameters
        )
        parts.append(f"{self.return_type_spelling} {self.name}({params_str})")

        if self.is_noexcept:
            parts.append("noexcept")

        return " ".join(parts)


@dataclass
class EnumValue:
    """A single enum value."""
    name: str
    value: Optional[int] = None
    description: str = ""


@dataclass
class EnumInfo:
    """Information about an enum."""
    name: str
    qualified_name: str
    is_scoped: bool = False  # enum class
    underlying_type: Optional[str] = None
    values: list[EnumValue] = field(default_factory=list)
    namespace: str = ""
    access: AccessSpecifier = AccessSpecifier.NONE
    location: Optional[SourceLocation] = None
    documentation: str = ""


@dataclass
class TypedefInfo:
    """Information about a typedef or using declaration."""
    name: str
    qualified_name: str
    underlying_type: str
    is_using: bool = False  # True for 'using', False for 'typedef'
    template_params: list[str] = field(default_factory=list)
    namespace: str = ""
    location: Optional[SourceLocation] = None
    documentation: str = ""


@dataclass
class MacroInfo:
    """Information about a preprocessor macro."""
    name: str
    definition: str
    parameters: list[str] = field(default_factory=list)  # For function-like macros
    is_function_like: bool = False
    location: Optional[SourceLocation] = None
    documentation: str = ""


@dataclass
class IncludeInfo:
    """Information about an #include directive."""
    path: str
    is_system: bool = False  # True for <>, False for ""
    resolved_path: Optional[Path] = None
    line: int = 0


@dataclass
class ClassInfo:
    """Information about a class or struct."""
    name: str
    qualified_name: str  # namespace::class_name
    kind: SymbolKind = SymbolKind.CLASS  # CLASS, STRUCT, or UNION
    namespace: str = ""
    base_classes: list[str] = field(default_factory=list)
    template_params: list[str] = field(default_factory=list)
    template_specialization_args: list[str] = field(default_factory=list)
    access: AccessSpecifier = AccessSpecifier.NONE  # For nested classes

    # Members
    methods: list[MethodInfo] = field(default_factory=list)
    members: list[MemberInfo] = field(default_factory=list)
    nested_classes: list["ClassInfo"] = field(default_factory=list)
    nested_enums: list[EnumInfo] = field(default_factory=list)
    typedefs: list[TypedefInfo] = field(default_factory=list)

    # Source location
    location: Optional[SourceLocation] = None

    # Documentation
    brief_description: str = ""  # Existing doxygen comment
    documentation: str = ""  # LLM-generated comprehensive documentation

    # Relationships (populated during analysis)
    derived_classes: list[str] = field(default_factory=list)
    used_by: list[str] = field(default_factory=list)
    uses: list[str] = field(default_factory=list)

    @property
    def is_template(self) -> bool:
        """Check if this is a template class."""
        return len(self.template_params) > 0

    @property
    def public_methods(self) -> list[MethodInfo]:
        """Get all public methods."""
        return [m for m in self.methods if m.access == AccessSpecifier.PUBLIC]

    @property
    def protected_methods(self) -> list[MethodInfo]:
        """Get all protected methods."""
        return [m for m in self.methods if m.access == AccessSpecifier.PROTECTED]

    @property
    def private_methods(self) -> list[MethodInfo]:
        """Get all private methods."""
        return [m for m in self.methods if m.access == AccessSpecifier.PRIVATE]

    @property
    def constructors(self) -> list[MethodInfo]:
        """Get all constructors."""
        return [m for m in self.methods if m.is_constructor]

    @property
    def destructor(self) -> Optional[MethodInfo]:
        """Get the destructor if present."""
        for m in self.methods:
            if m.is_destructor:
                return m
        return None

    def get_method_by_name(self, name: str) -> list[MethodInfo]:
        """Get all methods with the given name (handles overloads)."""
        return [m for m in self.methods if m.name == name]


@dataclass
class NamespaceInfo:
    """Information about a namespace."""
    name: str
    qualified_name: str
    parent_namespace: str = ""
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    enums: list[EnumInfo] = field(default_factory=list)
    typedefs: list[TypedefInfo] = field(default_factory=list)
    nested_namespaces: list["NamespaceInfo"] = field(default_factory=list)
    location: Optional[SourceLocation] = None
    documentation: str = ""


@dataclass
class CppFileAnalysis:
    """Complete analysis of a C++ source file."""
    file_path: Path
    file_hash: str = ""  # For change detection

    # Preprocessor
    includes: list[IncludeInfo] = field(default_factory=list)
    macros: list[MacroInfo] = field(default_factory=list)

    # Top-level declarations
    namespaces: list[NamespaceInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)  # Top-level classes
    functions: list[FunctionInfo] = field(default_factory=list)  # Free functions
    enums: list[EnumInfo] = field(default_factory=list)
    typedefs: list[TypedefInfo] = field(default_factory=list)
    global_variables: list[MemberInfo] = field(default_factory=list)

    # Metadata
    line_count: int = 0
    parse_errors: list[str] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)

    # Documentation (file-level)
    file_documentation: str = ""  # LLM-generated overview

    @property
    def all_classes(self) -> list[ClassInfo]:
        """Get all classes including those in namespaces (recursive)."""
        result = list(self.classes)
        
        def collect_from_ns(ns: NamespaceInfo):
            result.extend(ns.classes)
            for child_ns in ns.nested_namespaces:
                collect_from_ns(child_ns)
                
        for ns in self.namespaces:
            collect_from_ns(ns)
            
        return result

    @property
    def all_functions(self) -> list[FunctionInfo]:
        """Get all functions including those in namespaces (recursive)."""
        result = list(self.functions)
        
        def collect_from_ns(ns: NamespaceInfo):
            result.extend(ns.functions)
            for child_ns in ns.nested_namespaces:
                collect_from_ns(child_ns)

        for ns in self.namespaces:
            collect_from_ns(ns)
            
        return result

    @property
    def symbol_count(self) -> int:
        """Get total number of documented symbols."""
        count = len(self.classes) + len(self.functions) + len(self.enums)
        for cls in self.classes:
            count += len(cls.methods) + len(cls.members)
        for ns in self.namespaces:
            count += len(ns.classes) + len(ns.functions)
            for cls in ns.classes:
                count += len(cls.methods) + len(cls.members)
        return count

    def get_class_by_name(self, name: str) -> Optional[ClassInfo]:
        """Find a class by name (checks all namespaces)."""
        for cls in self.all_classes:
            if cls.name == name or cls.qualified_name == name:
                return cls
        return None

    def get_dependencies(self) -> list[str]:
        """Get list of files this file depends on (from includes)."""
        return [inc.path for inc in self.includes if not inc.is_system]
