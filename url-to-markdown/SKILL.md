---
name: url-to-markdown
description: Convert web pages to clean markdown by extracting text content organized by HTML structure while ignoring JavaScript, CSS, and other non-content elements. Use when the user wants to capture web page content for processing, convert a URL to markdown format, extract readable text from HTML pages, or save web content as markdown files.
---

# URL to Markdown Converter

Convert any web page to clean, readable markdown by extracting text content organized by HTML structure.

## Quick Start

```bash
python scripts/url_to_markdown.py <url> [output_file]
```

## Features

The converter:
- Extracts text content following HTML document structure
- Preserves headings (h1-h6) as markdown headers
- Converts links to markdown link syntax with absolute URLs
- Converts images to markdown image syntax
- Handles lists (ordered and unordered) with nesting
- Converts tables to markdown tables
- Preserves code blocks and inline code
- Handles blockquotes
- Removes all JavaScript, CSS, style tags, and non-content elements
- Auto-detects main content area (main, article, #content)

## Pattern Detection (Auto-Tables)

The converter automatically detects repeated similar elements (cards, list items, search results) and converts them into structured markdown tables.

**What it detects:**
- Repeated sibling elements with similar HTML structure
- Percentage values (ratings, scores)
- Links with text
- Dates (Jan 15, 12/25/2024 formats)
- Numbers

**Example:** A page with movie cards containing ratings and titles becomes:

| Rating 1 | Rating 2 | Name | Date |
| --- | --- | --- | --- |
| 95% | 88% | [Movie Title](url) | Jan 15 |

**Disable pattern detection:**
```bash
python scripts/url_to_markdown.py https://example.com --no-tables
```

## Usage Examples

**Print to stdout:**
```bash
python scripts/url_to_markdown.py https://example.com
```

**Save to file:**
```bash
python scripts/url_to_markdown.py https://example.com output.md
```

**With timeout:**
```bash
python scripts/url_to_markdown.py https://example.com --timeout 60
```

## Programmatic Usage

```python
from url_to_markdown import url_to_markdown, html_to_markdown

# From URL
markdown = url_to_markdown("https://example.com")

# From HTML string
html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
markdown = html_to_markdown(html, base_url="https://example.com")
```

## Elements Removed

The converter strips these non-content elements:
- `<script>` - JavaScript
- `<style>` - CSS
- `<noscript>` - NoScript fallbacks
- `<iframe>` - Embedded frames
- `<svg>`, `<canvas>` - Graphics
- `<video>`, `<audio>` - Media players
- `<head>`, `<meta>`, `<link>` - Document metadata
- Hidden elements (display:none, visibility:hidden, hidden attribute)

## Output Format

The output is standard markdown with:
- `#` through `######` for headings
- `**bold**` and `*italic*` formatting
- `[text](url)` links
- `![alt](src)` images
- `-` for unordered lists, `1.` for ordered lists
- `>` for blockquotes
- Triple backticks for code blocks
- Pipe tables for HTML tables
