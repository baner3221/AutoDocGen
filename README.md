# AutoDocGen

**Offline C++ Codebase Documentation Generator with Local LLM Semantic Analysis**

A privacy-first, fully offline documentation system designed for large C++ codebases (Android native services, Linux kernel drivers) that generates comprehensive semantic documentation with interactive class diagrams, served as a local wiki.

## 🔒 Key Features

| Feature | Description |
|---------|-------------|
| **100% Offline** | No internet connectivity required at runtime |
| **Privacy-First** | Your code never leaves your machine |
| **Local LLM** | All AI inference runs locally via Ollama |
| **Large File Support** | Handles 30K+ line files via intelligent chunking |
| **Comprehensive Docs** | Detailed parameter, dependency, and cross-reference documentation |
| **Interactive Wiki** | Local web server with file tree navigation |
| **Class Diagrams** | Graphviz-generated UML diagrams with hyperlinks |
| **Incremental Updates** | File watcher for automatic documentation updates |

## 📋 Requirements

- **Python**: 3.11+
- **Ollama**: Running locally with a code model
- **libclang**: For C++ parsing
- **Graphviz**: For diagram generation (optional)

## 🚀 Quick Start

### 1. Install AutoDocGen

```bash
cd AutoDocGen
pip install -e .
```

### 2. Install and run Ollama

```bash
# Install Ollama from https://ollama.ai
# Pull a code model
ollama pull qwen2.5-coder:32b
```

### 3. Generate Documentation

```bash
# Initialize documentation for a codebase
autodocgen init /path/to/android/native/library

# Start the documentation server
autodocgen serve

# Open http://127.0.0.1:8080 in your browser
```

## 📖 Usage

### Initialize Documentation

```bash
autodocgen init /path/to/codebase --output ./docs --model qwen2.5-coder:32b
```

### Serve Documentation

```bash
autodocgen serve --port 8080 --docs ./docs
```

### Watch for Changes

```bash
autodocgen watch /path/to/codebase --output ./docs
```

### Analyze a Single File

```bash
autodocgen analyze /path/to/file.cpp --output ./output.md
```

### Verify Offline Mode

```bash
autodocgen verify-offline
```

## 🏗️ Documentation Quality

Unlike brief 1-2 sentence descriptions, AutoDocGen generates **comprehensive documentation**:

### For Each Function/Method:
- **Detailed description** (2-4 paragraphs)
- **Parameters**: Purpose, valid values, ownership semantics
- **Return values**: All possible states, error conditions
- **Dependencies**: Cross-referenced with links to other class docs
- **Side effects**: State modifications, locks, I/O
- **Usage context**: When called, prerequisites
- **Code examples**
- **Mermaid diagrams** for complex flows

### For Each Class:
- **Overview** with design rationale
- **Class diagrams** showing inheritance and relationships
- **All methods** documented in detail
- **Member variables** with invariants
- **Usage examples**

## 🔧 Configuration

Create `autodocgen.config.json`:

```json
{
  "codebase_path": "/path/to/android/frameworks/native",
  "output_path": "./docs",
  "llm": {
    "backend": "ollama",
    "model_name": "qwen2.5-coder:32b",
    "temperature": 0.1
  },
  "parser": {
    "compile_flags": ["-std=c++17", "-DANDROID"],
    "exclude_patterns": ["**/test/**", "**/third_party/**"]
  }
}
```

## 📁 Project Structure

```
AutoDocGen/
├── src/autodocgen/
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration
│   ├── analyzer.py          # Main pipeline orchestrator
│   ├── parser/              # C++ parsing (libclang)
│   ├── chunker/             # Large file chunking
│   ├── llm/                 # Ollama integration
│   ├── generator/           # Markdown & diagram generation
│   ├── web/                 # Flask wiki server
│   ├── watcher.py           # File change monitoring
│   └── storage/             # SQLite database
├── pyproject.toml
├── README.md
└── PROJECT_OUTLINE.md
```

## 🎯 Recommended LLM Models

### For Limited Hardware (Default)

| Model | Size | RAM Required | Best For |
|-------|------|--------------|----------|
| **Qwen2.5-Coder 7B** | 7B | 8GB | Default choice, good quality/speed balance |
| **DeepSeek Coder 1.3B** | 1.3B | 4GB | Very limited hardware, basic docs |
| **CodeLlama 7B** | 7B | 8GB | Stable alternative |

```bash
# Recommended for low hardware (default)
ollama pull qwen2.5-coder:7b

# For very limited hardware (4GB RAM)
ollama pull deepseek-coder:1.3b
```

### For High-End Hardware

| Model | Size | RAM Required | Best For |
|-------|------|--------------|----------|
| **Qwen2.5-Coder 32B** | 32B | 40GB | Maximum quality, large context |
| **DeepSeek Coder V2 16B** | 16B | 20GB | Good balance for capable hardware |

```bash
# High quality (requires 40GB+ RAM)
autodocgen init /path/to/code --model qwen2.5-coder:32b --high-resource
```

## 🪶 Low Resource Mode

By default, AutoDocGen runs in **low resource mode** optimized for limited hardware:

| Setting | Low Resource | High Resource |
|---------|--------------|---------------|
| Default Model | 7B | 32B |
| Context Window | 4,096 tokens | 65,536 tokens |
| Max Output | 1,024 tokens | 8,192 tokens |
| Chunk Size | 300 lines | 600 lines |

To switch modes:

```bash
# Low resource (default)
autodocgen init /path/to/code

# High resource (for powerful machines)
autodocgen init /path/to/code --high-resource --model qwen2.5-coder:32b
```

## 🔐 Security & Privacy

- All network communication is **localhost only** by default
- **No telemetry**, analytics, or crash reports
- **No external CDN** dependencies (all assets bundled)
- Optional `--allow-network` flag for LAN access

## 📄 License

MIT License
