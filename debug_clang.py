
import sys
from pathlib import Path
from clang.cindex import Index, Config, CursorKind, TranslationUnit

# Configure clang path if needed (AutoDocGen usually handles this, assume it's in path or handled)
# If this fails, I might need to replicate config.

def walk(cursor, depth=0):
    indent = "  " * depth
    try:
        loc = cursor.location
        filename = loc.file.name if loc.file else "None"
        line = loc.line
        print(f"{indent}{cursor.kind} : {cursor.spelling} [{filename}:{line}]")
    except:
        print(f"{indent}{cursor.kind} : {cursor.spelling} [Error getting loc]")
    
    for child in cursor.get_children():
        walk(child, depth + 1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_clang.py <file>")
        return

    fpath = Path(sys.argv[1]).resolve()
    print(f"Parsing: {fpath}")

    index = Index.create()
    args = ["-x", "c++", f"-I{fpath.parent}", f"-I{fpath.parent.parent}/include"] 
    # Add include paths roughly

    tu = index.parse(str(fpath), args=args)
    
    print("Diagnostics:")
    for diag in tu.diagnostics:
        print(diag)
        
    print("\nAST:")
    walk(tu.cursor)

if __name__ == "__main__":
    main()
