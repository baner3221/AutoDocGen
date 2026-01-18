"""
Flask application for serving documentation locally.

SECURITY: Binds to localhost only by default.
All assets are bundled locally - no external CDN dependencies.
"""

from pathlib import Path
from flask import Flask, render_template, send_from_directory, abort, request
import markdown
import re


def create_app(docs_path: Path) -> Flask:
    """
    Create the Flask application for serving documentation.

    Args:
        docs_path: Path to the generated documentation

    Returns:
        Configured Flask application
    """
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # Ensure docs path exists
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)

    @app.route("/")
    def index():
        """Serve the main index page."""
        index_file = docs_path / "index.md"

        if index_file.exists():
            content = index_file.read_text(encoding="utf-8")
            html_content = render_markdown(content, docs_path)
            return render_template(
                "base.html",
                title="AutoDocGen Documentation",
                content=html_content,
                tree=get_file_tree(docs_path),
            )

        return render_template(
            "base.html",
            title="AutoDocGen Documentation",
            content="<p>No documentation generated yet. Run <code>autodocgen init</code> first.</p>",
            tree=get_file_tree(docs_path),
        )

    @app.route("/docs/<path:filepath>")
    def serve_doc(filepath: str):
        """Serve a documentation file."""
        file_path = docs_path / filepath

        # Handle markdown files
        if filepath.endswith(".md"):
            if not file_path.exists():
                abort(404)

            content = file_path.read_text(encoding="utf-8")
            html_content = render_markdown(content, file_path.parent)

            title = extract_title(content) or filepath

            return render_template(
                "base.html",
                title=title,
                content=html_content,
                tree=get_file_tree(docs_path),
                current_path=filepath,
            )

        # Handle other files (images, etc.)
        if file_path.exists():
            return send_from_directory(
                str(docs_path),
                filepath,
            )

        abort(404)

    @app.route("/diagrams/<path:filepath>")
    def serve_diagram(filepath: str):
        """Serve diagram files."""
        diagram_path = docs_path / "diagrams" / filepath

        if diagram_path.exists():
            return send_from_directory(
                str(docs_path / "diagrams"),
                filepath,
            )

        abort(404)

    @app.route("/search")
    def search():
        """Search documentation."""
        query = request.args.get("q", "").strip()

        if not query:
            return render_template(
                "search.html",
                query="",
                results=[],
                tree=get_file_tree(docs_path),
            )

        results = search_docs(docs_path, query)

        return render_template(
            "search.html",
            query=query,
            results=results,
            tree=get_file_tree(docs_path),
        )

    @app.route("/static/<path:filepath>")
    def serve_static(filepath: str):
        """Serve static assets."""
        return send_from_directory(app.static_folder, filepath)

    @app.route("/diagrams")
    def diagrams():
        """Serve the codebase overview diagram."""
        # Look for codebase_overview.md
        diagram_path = docs_path / "diagrams" / "codebase_overview.md"
        
        if not diagram_path.exists():
            # Fallback to checking if there are any SVGs
            diagram_path_svg = docs_path / "diagrams" / "codebase_overview.svg"
            if diagram_path_svg.exists():
                return send_from_directory(
                    str(docs_path / "diagrams"),
                    "codebase_overview.svg",
                )
            
            return render_template(
                "base.html",
                title="Diagrams",
                content="<h1>Codebase Diagrams</h1><p>No diagrams generated yet. Run <code>autodocgen diagrams</code> to generate them.</p><p><small>Note: Install Graphviz (dot) for static SVG generation.</small></p>",
                tree=get_file_tree(docs_path),
                current_path="/diagrams"
            )
            
        content = diagram_path.read_text(encoding="utf-8")
        
        # Extract raw mermaid source from the div wrapper
        # Previous format: <div class="mermaid">\nSOURCE\n</div>
        match = re.search(r'<div class="mermaid">\s*(.*?)\s*</div>', content, re.DOTALL)
        if match:
            diagram_source = match.group(1)
        else:
            # Fallback if format is different (e.g. legacy markdown fence)
            match_fence = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
            diagram_source = match_fence.group(1) if match_fence else "graph TD; A[Error: Could not parse diagram source];"

        return render_template(
            "diagram_viewer.html",
            title="Codebase Diagrams",
            diagram_source=diagram_source,
            tree=get_file_tree(docs_path),
            current_path="/diagrams"
        )

    return app


def render_markdown(content: str, base_path: Path) -> str:
    """
    Render Markdown content to HTML.

    Args:
        content: Markdown content
        base_path: Base path for resolving relative links

    Returns:
        HTML content
    """
    # Extensions for better rendering
    extensions = [
        "fenced_code",
        "codehilite",
        "tables",
        "toc",
        "nl2br",
        "sane_lists",
    ]

    extension_configs = {
        "codehilite": {
            "css_class": "highlight",
            "guess_lang": False,
        },
        "toc": {
            "permalink": True,
            "toc_depth": 3,
        },
    }

    # Convert internal links
    content = convert_internal_links(content)

    # Render markdown
    html = markdown.markdown(
        content,
        extensions=extensions,
        extension_configs=extension_configs,
    )

    # Process Mermaid diagrams
    html = process_mermaid(html)

    return html


def convert_internal_links(content: str) -> str:
    """Convert internal .md links to /docs/ routes."""
    # Match markdown links to .md files
    pattern = r'\[([^\]]+)\]\(([^)]+\.md)(#[^)]*)?\)'

    def replace_link(match):
        text = match.group(1)
        path = match.group(2)
        anchor = match.group(3) or ""

        # Convert to /docs/ route
        if not path.startswith("http"):
            return f'[{text}](/docs/{path}{anchor})'
        return match.group(0)

    return re.sub(pattern, replace_link, content)


def process_mermaid(html: str) -> str:
    """Convert Mermaid code blocks to renderable divs."""
    # Match <pre><code class="language-mermaid">...</code></pre>
    pattern = r'<pre><code class="language-mermaid">(.*?)</code></pre>'

    def replace_mermaid(match):
        diagram = match.group(1)
        return f'<div class="mermaid">{diagram}</div>'

    return re.sub(pattern, replace_mermaid, html, flags=re.DOTALL)


def extract_title(content: str) -> str:
    """Extract the title from Markdown content."""
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def get_file_tree(docs_path: Path) -> list:
    """
    Build a file tree structure for navigation.

    Returns:
        List of tree nodes
    """
    tree = []

    def add_to_tree(path: Path, node_list: list, base: Path):
        """Recursively add items to the tree."""
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

        for item in items:
            if item.name.startswith("."):
                continue

            relative = item.relative_to(base)

            if item.is_dir():
                children = []
                add_to_tree(item, children, base)
                if children:  # Only add directories with content
                    node_list.append({
                        "name": item.name,
                        "type": "directory",
                        "path": str(relative),
                        "children": children,
                    })
            elif item.suffix == ".md":
                node_list.append({
                    "name": item.stem,
                    "type": "file",
                    "path": f"/docs/{relative}",
                })
            elif item.suffix in [".svg", ".png"]:
                node_list.append({
                    "name": item.stem,
                    "type": "diagram",
                    "path": f"/docs/{relative}",
                })

    if docs_path.exists():
        add_to_tree(docs_path, tree, docs_path)

    # Add Diagrams link explicitly at the top
    tree.insert(0, {
        "name": "Codebase Diagrams",
        "type": "diagram",
        "path": "/diagrams",
        "children": []
    })
    
    return tree


    return app


def search_docs(docs_path: Path, query: str) -> list:
    """
    Search documentation files for a query.

    Args:
        docs_path: Path to documentation
        query: Search query

    Returns:
        List of search results
    """
    results = []
    query_lower = query.lower()

    for md_file in docs_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            content_lower = content.lower()

            if query_lower in content_lower:
                # Find matching context
                idx = content_lower.index(query_lower)
                start = max(0, idx - 50)
                end = min(len(content), idx + len(query) + 50)
                context = content[start:end]

                if start > 0:
                    context = "..." + context
                if end < len(content):
                    context = context + "..."

                relative = md_file.relative_to(docs_path)
                title = extract_title(content) or md_file.stem

                results.append({
                    "title": title,
                    "path": f"/docs/{relative}",
                    "context": context,
                })

                if len(results) >= 50:  # Limit results
                    break
        except Exception:
            continue

    return results
