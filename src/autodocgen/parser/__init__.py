"""
Parser module for C++ code analysis.
"""

from autodocgen.parser.cpp_parser import CppParser
from autodocgen.parser.models import (
    CppFileAnalysis,
    ClassInfo,
    MethodInfo,
    FunctionInfo,
    ParameterInfo,
    MemberInfo,
    EnumInfo,
    NamespaceInfo,
    IncludeInfo,
    MacroInfo,
    TypedefInfo,
)

__all__ = [
    "CppParser",
    "CppFileAnalysis",
    "ClassInfo",
    "MethodInfo",
    "FunctionInfo",
    "ParameterInfo",
    "MemberInfo",
    "EnumInfo",
    "NamespaceInfo",
    "IncludeInfo",
    "MacroInfo",
    "TypedefInfo",
]
