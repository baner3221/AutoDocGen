import sys
from pathlib import Path
from autodocgen.config import get_default_config
from autodocgen.analyzer import CodebaseAnalyzer

def debug_llm_generation():
    # Use the file that failed
    file_path = Path(r"C:\Users\Neelanjan\libcamera\external_libcamera-master\src\gstreamer\gstlibcameraallocator.h")
    
    # Setup config
    codebase = file_path.parent
    config = get_default_config(codebase)
    config.llm.low_resource_mode = True # Mimic user
    
    # Initialize analyzer
    print(f"Initializing analyzer for: {file_path}")
    analyzer = CodebaseAnalyzer(config)
    
    try:
        # Parse
        print("Parsing...")
        analysis = analyzer.parser.parse_file(file_path)
        print(f"Parsing complete. Found {len(analysis.all_functions)} functions.")
        
        # Document (This is where it fails)
        print("Starting documentation generation...")
        
        # Manually call _document_file to see errors
        analyzer._document_file(file_path, analysis)
        
        # Check results
        chunks = analyzer.chunker.chunk_file(file_path, analysis, analyzer.parser._source_code)
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i}: Processed={chunk.is_processed}")
            if hasattr(chunk, 'llm_response'):
                print(f"Response prefix: {chunk.llm_response[:50]}...")
            else:
                print("No response attribute.")

    except Exception as e:
        print(f"EXCEPTION CAUGHT: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_llm_generation()
