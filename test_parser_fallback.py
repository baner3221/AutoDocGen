"""Test the regex fallback parser on CameraBufferManager.cpp."""
from pathlib import Path
from autodocgen.config import Config
from autodocgen.parser.cpp_parser import CppParser

def test_parser():
    config = Config(
        codebase_path=Path("tests/graphics_buffer_lib"),
        output_path=Path("docs_graphics_lib")
    )
    
    parser = CppParser(config)
    
    # Test CameraBufferManager.cpp - known to have parsing issues
    target = Path("tests/graphics_buffer_lib/src/CameraBufferManager.cpp").absolute()
    print(f"Parsing: {target}")
    
    analysis = parser.parse_file(target)
    
    print(f"\nResults:")
    print(f"  Functions found: {len(analysis.functions)}")
    print(f"  Classes found: {len(analysis.classes)}")
    print(f"  Parse errors: {len(analysis.parse_errors)}")
    
    if analysis.parse_errors:
        print(f"\nParse errors (first 3):")
        for err in analysis.parse_errors[:3]:
            print(f"  - {err[:80]}...")
    
    print(f"\nFunctions extracted:")
    for func in analysis.functions[:15]:  # Show first 15
        loc = func.location
        line_range = f"L{loc.line_start}-{loc.line_end}" if loc else "?"
        print(f"  - {func.qualified_name} ({line_range})")
    
    if len(analysis.functions) > 15:
        print(f"  ... and {len(analysis.functions) - 15} more")

if __name__ == "__main__":
    test_parser()
