"""
C++ Parser using libclang for accurate semantic analysis.

This parser extracts comprehensive structural information from C++ source files
including classes, methods, functions, templates, and their relationships.
"""

import hashlib
from pathlib import Path
from typing import Optional

from clang.cindex import (
    Config as ClangConfig,
    Index,
    TranslationUnit,
    Cursor,
    CursorKind,
    AccessSpecifier as ClangAccess,
    TypeKind,
)

from autodocgen.config import Config
from autodocgen.parser.models import (
    CppFileAnalysis,
    ClassInfo,
    MethodInfo,
    FunctionInfo,
    ParameterInfo,
    MemberInfo,
    EnumInfo,
    EnumValue,
    NamespaceInfo,
    IncludeInfo,
    MacroInfo,
    TypedefInfo,
    SourceLocation,
    AccessSpecifier,
    SymbolKind,
)


def _convert_access(clang_access: ClangAccess) -> AccessSpecifier:
    """Convert clang access specifier to our enum."""
    mapping = {
        ClangAccess.PUBLIC: AccessSpecifier.PUBLIC,
        ClangAccess.PROTECTED: AccessSpecifier.PROTECTED,
        ClangAccess.PRIVATE: AccessSpecifier.PRIVATE,
    }
    return mapping.get(clang_access, AccessSpecifier.NONE)


def _get_source_location(cursor: Cursor) -> Optional[SourceLocation]:
    """Extract source location from a cursor."""
    if not cursor.location.file:
        return None

    extent = cursor.extent
    return SourceLocation(
        file_path=Path(cursor.location.file.name),
        line_start=extent.start.line,
        line_end=extent.end.line,
        column_start=extent.start.column,
        column_end=extent.end.column,
    )


def _get_code_text(cursor: Cursor, source_code: str) -> str:
    """Extract the actual source code for a cursor."""
    if not cursor.extent:
        return ""

    lines = source_code.splitlines()
    start_line = cursor.extent.start.line - 1
    end_line = cursor.extent.end.line

    if start_line < 0 or end_line > len(lines):
        return ""

    extracted_lines = lines[start_line:end_line]
    return "\n".join(extracted_lines)


class CppParser:
    """
    Parser for C++ source files using libclang.

    Extracts comprehensive structural and semantic information from C++ code
    including classes, functions, templates, and their relationships.
    """

    def __init__(self, config: Config):
        """
        Initialize the C++ parser.

        Args:
            config: AutoDocGen configuration
        """
        self.config = config
        self.index = Index.create()
        self._source_code: str = ""

    def parse_file(self, file_path: Path) -> CppFileAnalysis:
        """
        Parse a single C++ file and extract its structure.

        Args:
            file_path: Path to the C++ file to parse

        Returns:
            CppFileAnalysis containing all extracted information
        """
        # Read source code
        self._source_code = file_path.read_text(encoding="utf-8", errors="replace")
        file_hash = hashlib.sha256(self._source_code.encode()).hexdigest()[:16]
        line_count = len(self._source_code.splitlines())

        # Build compile arguments
        compile_args = list(self.config.parser.compile_flags)
        
        # Force C++ language mode (critical for .h files)
        compile_args.extend(["-x", "c++"])
        
        for include_path in self.config.parser.include_paths:
            compile_args.append(f"-I{include_path}")

        # Parse with libclang
        try:
            tu = self.index.parse(
                str(file_path),
                args=compile_args,
                options=(
                    TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD |
                    TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
                ),
            )
        except Exception as e:
            return CppFileAnalysis(
                file_path=file_path,
                file_hash=file_hash,
                line_count=line_count,
                parse_errors=[str(e)],
            )

        # Collect parse diagnostics
        parse_errors = []
        parse_warnings = []
        for diag in tu.diagnostics:
            msg = f"{diag.location.file}:{diag.location.line}: {diag.spelling}"
            if diag.severity >= 3:  # Error or Fatal
                parse_errors.append(msg)
            elif diag.severity == 2:  # Warning
                parse_warnings.append(msg)

        # Extract structure
        analysis = CppFileAnalysis(
            file_path=file_path,
            file_hash=file_hash,
            line_count=line_count,
            parse_errors=parse_errors,
            parse_warnings=parse_warnings,
        )

        # Walk the AST
        self._process_cursor(tu.cursor, analysis, file_path)

        return analysis

    def _process_cursor(
        self,
        cursor: Cursor,
        analysis: CppFileAnalysis,
        target_file: Path,
        current_namespace: str = "",
        current_class: Optional[ClassInfo] = None,
    ) -> None:
        """
        Recursively process a cursor and its children.

        Args:
            cursor: Current clang cursor
            analysis: Analysis object to populate
            target_file: File being analyzed (skip cursors from other files)
            current_namespace: Current namespace context
            current_class: Current class context (for nested items)
        """
        for child in cursor.get_children():
            # Skip if not from our file
            if child.location.file and Path(child.location.file.name) != target_file:
                continue

            kind = child.kind

            # Namespaces
            if kind == CursorKind.NAMESPACE:
                ns_name = child.spelling
                qualified = f"{current_namespace}::{ns_name}" if current_namespace else ns_name

                ns_info = NamespaceInfo(
                    name=ns_name,
                    qualified_name=qualified,
                    parent_namespace=current_namespace,
                    location=_get_source_location(child),
                )
                analysis.namespaces.append(ns_info)

                # Process namespace contents
                self._process_namespace(child, ns_info, analysis, target_file, qualified)

            # Classes and Structs
            elif kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL, CursorKind.UNION_DECL):
                if child.is_definition():
                    class_info = self._process_class(child, current_namespace)
                    if current_class:
                        current_class.nested_classes.append(class_info)
                    else:
                        analysis.classes.append(class_info)

            # Free functions
            elif kind == CursorKind.FUNCTION_DECL:
                func_info = self._process_function(child, current_namespace)
                analysis.functions.append(func_info)

            # Enums
            elif kind == CursorKind.ENUM_DECL:
                if child.is_definition():
                    enum_info = self._process_enum(child, current_namespace)
                    analysis.enums.append(enum_info)

            # Typedefs and using declarations
            elif kind in (CursorKind.TYPEDEF_DECL, CursorKind.TYPE_ALIAS_DECL):
                typedef_info = self._process_typedef(child, current_namespace)
                analysis.typedefs.append(typedef_info)

            # Includes
            elif kind == CursorKind.INCLUSION_DIRECTIVE:
                include_info = self._process_include(child)
                analysis.includes.append(include_info)

            # Macros
            elif kind == CursorKind.MACRO_DEFINITION:
                macro_info = self._process_macro(child)
                analysis.macros.append(macro_info)

            # Global variables
            elif kind == CursorKind.VAR_DECL:
                var_info = self._process_variable(child)
                analysis.global_variables.append(var_info)

    def _process_namespace(
        self,
        cursor: Cursor,
        ns_info: NamespaceInfo,
        analysis: CppFileAnalysis,
        target_file: Path,
        current_namespace: str,
    ) -> None:
        """Process contents of a namespace."""
        for child in cursor.get_children():
            if child.location.file and Path(child.location.file.name) != target_file:
                continue

            kind = child.kind

            if kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
                if child.is_definition():
                    class_info = self._process_class(child, current_namespace)
                    ns_info.classes.append(class_info)

            elif kind == CursorKind.FUNCTION_DECL:
                func_info = self._process_function(child, current_namespace)
                ns_info.functions.append(func_info)

            elif kind == CursorKind.ENUM_DECL:
                if child.is_definition():
                    enum_info = self._process_enum(child, current_namespace)
                    ns_info.enums.append(enum_info)

            elif kind in (CursorKind.TYPEDEF_DECL, CursorKind.TYPE_ALIAS_DECL):
                typedef_info = self._process_typedef(child, current_namespace)
                ns_info.typedefs.append(typedef_info)

            elif kind == CursorKind.NAMESPACE:
                nested_ns_name = child.spelling
                nested_qualified = f"{current_namespace}::{nested_ns_name}"
                nested_ns = NamespaceInfo(
                    name=nested_ns_name,
                    qualified_name=nested_qualified,
                    parent_namespace=current_namespace,
                    location=_get_source_location(child),
                )
                ns_info.nested_namespaces.append(nested_ns)
                self._process_namespace(child, nested_ns, analysis, target_file, nested_qualified)

    def _process_class(self, cursor: Cursor, namespace: str) -> ClassInfo:
        """Process a class/struct definition."""
        name = cursor.spelling
        qualified = f"{namespace}::{name}" if namespace else name

        kind_map = {
            CursorKind.CLASS_DECL: SymbolKind.CLASS,
            CursorKind.STRUCT_DECL: SymbolKind.STRUCT,
            CursorKind.UNION_DECL: SymbolKind.UNION,
        }

        class_info = ClassInfo(
            name=name,
            qualified_name=qualified,
            kind=kind_map.get(cursor.kind, SymbolKind.CLASS),
            namespace=namespace,
            location=_get_source_location(cursor),
            brief_description=cursor.brief_comment or "",
        )

        # Extract template parameters
        class_info.template_params = self._get_template_params(cursor)

        # Process class members
        current_access = AccessSpecifier.PRIVATE if cursor.kind == CursorKind.CLASS_DECL else AccessSpecifier.PUBLIC

        for child in cursor.get_children():
            kind = child.kind

            # Access specifiers
            if kind == CursorKind.CXX_ACCESS_SPEC_DECL:
                current_access = _convert_access(child.access_specifier)

            # Base classes
            elif kind == CursorKind.CXX_BASE_SPECIFIER:
                base_name = child.type.spelling
                class_info.base_classes.append(base_name)

            # Methods (including constructors/destructors)
            elif kind in (
                CursorKind.CXX_METHOD,
                CursorKind.CONSTRUCTOR,
                CursorKind.DESTRUCTOR,
                CursorKind.CONVERSION_FUNCTION,
            ):
                method_info = self._process_method(child, current_access)
                class_info.methods.append(method_info)

            # Member variables
            elif kind == CursorKind.FIELD_DECL:
                member_info = self._process_member(child, current_access)
                class_info.members.append(member_info)

            # Nested classes
            elif kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
                if child.is_definition():
                    nested_class = self._process_class(child, qualified)
                    nested_class.access = current_access
                    class_info.nested_classes.append(nested_class)

            # Nested enums
            elif kind == CursorKind.ENUM_DECL:
                if child.is_definition():
                    enum_info = self._process_enum(child, qualified)
                    enum_info.access = current_access
                    class_info.nested_enums.append(enum_info)

            # Typedefs within class
            elif kind in (CursorKind.TYPEDEF_DECL, CursorKind.TYPE_ALIAS_DECL):
                typedef_info = self._process_typedef(child, qualified)
                class_info.typedefs.append(typedef_info)

        return class_info

    def _process_method(self, cursor: Cursor, access: AccessSpecifier) -> MethodInfo:
        """Process a method declaration."""
        name = cursor.spelling
        result_type = cursor.result_type

        method_info = MethodInfo(
            name=name,
            return_type=result_type.spelling if result_type else "void",
            return_type_spelling=result_type.spelling if result_type else "void",
            access=access,
            is_virtual=cursor.is_virtual_method(),
            is_pure_virtual=cursor.is_pure_virtual_method(),
            is_static=cursor.is_static_method(),
            is_const=cursor.is_const_method(),
            is_constructor=cursor.kind == CursorKind.CONSTRUCTOR,
            is_destructor=cursor.kind == CursorKind.DESTRUCTOR,
            location=_get_source_location(cursor),
            brief_description=cursor.brief_comment or "",
            body_code=_get_code_text(cursor, self._source_code),
        )

        # Check for override/final
        for child in cursor.get_children():
            if child.kind == CursorKind.CXX_OVERRIDE_ATTR:
                method_info.is_override = True
            elif child.kind == CursorKind.CXX_FINAL_ATTR:
                method_info.is_final = True

        # Process parameters
        method_info.parameters = self._process_parameters(cursor)

        # Template parameters
        method_info.template_params = self._get_template_params(cursor)

        return method_info

    def _process_function(self, cursor: Cursor, namespace: str) -> FunctionInfo:
        """Process a free function declaration."""
        name = cursor.spelling
        qualified = f"{namespace}::{name}" if namespace else name
        result_type = cursor.result_type

        func_info = FunctionInfo(
            name=name,
            qualified_name=qualified,
            return_type=result_type.spelling if result_type else "void",
            return_type_spelling=result_type.spelling if result_type else "void",
            namespace=namespace,
            is_static=cursor.storage_class.name == "STATIC",
            location=_get_source_location(cursor),
            brief_description=cursor.brief_comment or "",
            body_code=_get_code_text(cursor, self._source_code),
        )

        # Process parameters
        func_info.parameters = self._process_parameters(cursor)

        # Template parameters
        func_info.template_params = self._get_template_params(cursor)

        return func_info

    def _process_parameters(self, cursor: Cursor) -> list[ParameterInfo]:
        """Process function/method parameters."""
        params = []
        for child in cursor.get_children():
            if child.kind == CursorKind.PARM_DECL:
                param_type = child.type

                param_info = ParameterInfo(
                    name=child.spelling or f"arg{len(params)}",
                    type_name=param_type.spelling,
                    type_spelling=param_type.spelling,
                    is_const=param_type.is_const_qualified(),
                    is_reference=param_type.kind == TypeKind.LVALUEREFERENCE,
                    is_rvalue_ref=param_type.kind == TypeKind.RVALUEREFERENCE,
                    is_pointer=param_type.kind == TypeKind.POINTER,
                )

                # Check for default value
                tokens = list(child.get_tokens())
                for i, token in enumerate(tokens):
                    if token.spelling == "=":
                        default_parts = [t.spelling for t in tokens[i + 1:]]
                        param_info.default_value = " ".join(default_parts)
                        break

                params.append(param_info)

        return params

    def _process_member(self, cursor: Cursor, access: AccessSpecifier) -> MemberInfo:
        """Process a class member variable."""
        member_type = cursor.type

        return MemberInfo(
            name=cursor.spelling,
            type_name=member_type.spelling,
            type_spelling=member_type.spelling,
            access=access,
            is_static=cursor.storage_class.name == "STATIC",
            is_const=member_type.is_const_qualified(),
            is_mutable="mutable" in cursor.displayname,
            location=_get_source_location(cursor),
        )

    def _process_enum(self, cursor: Cursor, namespace: str) -> EnumInfo:
        """Process an enum declaration."""
        name = cursor.spelling
        qualified = f"{namespace}::{name}" if namespace else name

        enum_info = EnumInfo(
            name=name,
            qualified_name=qualified,
            is_scoped=cursor.is_scoped_enum(),
            namespace=namespace,
            location=_get_source_location(cursor),
        )

        # Get underlying type
        if cursor.enum_type:
            enum_info.underlying_type = cursor.enum_type.spelling

        # Get enum values
        for child in cursor.get_children():
            if child.kind == CursorKind.ENUM_CONSTANT_DECL:
                enum_info.values.append(EnumValue(
                    name=child.spelling,
                    value=child.enum_value,
                ))

        return enum_info

    def _process_typedef(self, cursor: Cursor, namespace: str) -> TypedefInfo:
        """Process a typedef or using declaration."""
        name = cursor.spelling
        qualified = f"{namespace}::{name}" if namespace else name

        underlying = cursor.underlying_typedef_type
        return TypedefInfo(
            name=name,
            qualified_name=qualified,
            underlying_type=underlying.spelling if underlying else "",
            is_using=cursor.kind == CursorKind.TYPE_ALIAS_DECL,
            namespace=namespace,
            location=_get_source_location(cursor),
        )

    def _process_include(self, cursor: Cursor) -> IncludeInfo:
        """Process an include directive."""
        try:
            included_file = cursor.get_included_file()
        except (AssertionError, Exception):
            included_file = None

        return IncludeInfo(
            path=included_file.name if included_file else cursor.displayname,
            is_system=cursor.displayname.startswith("<"),
            resolved_path=Path(included_file.name) if included_file else None,
            line=cursor.location.line,
        )

    def _process_macro(self, cursor: Cursor) -> MacroInfo:
        """Process a macro definition."""
        tokens = list(cursor.get_tokens())
        definition = " ".join(t.spelling for t in tokens[1:]) if len(tokens) > 1 else ""

        return MacroInfo(
            name=cursor.spelling,
            definition=definition,
            is_function_like=(
                cursor.is_macro_function_like() 
                if hasattr(cursor, 'is_macro_function_like') 
                else False
            ),
            location=_get_source_location(cursor),
        )

    def _process_variable(self, cursor: Cursor) -> MemberInfo:
        """Process a global variable."""
        var_type = cursor.type

        return MemberInfo(
            name=cursor.spelling,
            type_name=var_type.spelling,
            type_spelling=var_type.spelling,
            access=AccessSpecifier.NONE,
            is_static=cursor.storage_class.name == "STATIC",
            is_const=var_type.is_const_qualified(),
            location=_get_source_location(cursor),
        )

    def _get_template_params(self, cursor: Cursor) -> list[str]:
        """Extract template parameters from a cursor."""
        params = []
        for child in cursor.get_children():
            if child.kind in (
                CursorKind.TEMPLATE_TYPE_PARAMETER,
                CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
                CursorKind.TEMPLATE_TEMPLATE_PARAMETER,
            ):
                params.append(child.spelling)
        return params
