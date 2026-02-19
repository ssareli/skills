#!/usr/bin/env python3
"""
URL to Markdown Converter

Fetches a URL, extracts text content organized by HTML structure,
and converts it to clean markdown. Ignores JavaScript, CSS, and other junk.

Features pattern detection to automatically convert repeated similar elements
(like product cards, list items, search results) into markdown tables.

Usage:
    python url_to_markdown.py <url> [output_file]
    
Examples:
    python url_to_markdown.py https://example.com
    python url_to_markdown.py https://example.com output.md
    python url_to_markdown.py https://example.com --no-tables  # Disable pattern detection
"""

import sys
import re
import argparse
from urllib.parse import urljoin, urlparse
from collections import Counter

try:
    import requests
    from bs4 import BeautifulSoup, NavigableString, Comment, Tag
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "requests", "beautifulsoup4", "--break-system-packages", "-q"])
    import requests
    from bs4 import BeautifulSoup, NavigableString, Comment, Tag


# Tags to completely remove (including their content)
REMOVE_TAGS = {
    'script', 'style', 'noscript', 'iframe', 'svg', 'canvas', 
    'video', 'audio', 'map', 'object', 'embed', 'applet',
    'head', 'meta', 'link', 'template', 'slot'
}

# Block-level tags that create structure
BLOCK_TAGS = {
    'p', 'div', 'section', 'article', 'header', 'footer', 'main', 'aside',
    'nav', 'figure', 'figcaption', 'blockquote', 'pre', 'address',
    'form', 'fieldset', 'table', 'thead', 'tbody', 'tfoot', 'tr',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd', 'details', 'summary'
}

# Heading tags
HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

# Minimum siblings needed to detect a pattern
MIN_PATTERN_SIBLINGS = 3

# Enable pattern detection globally (can be disabled via CLI)
ENABLE_PATTERN_DETECTION = True


def fetch_url(url: str, timeout: int = 30) -> str:
    """Fetch HTML content from URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; URLToMarkdown/1.0)'
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def clean_text(text: str) -> str:
    """Clean and normalize whitespace in text."""
    if not text:
        return ""
    text = re.sub(r'[ \t]+', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)


def get_element_signature(element) -> tuple:
    """
    Generate a structural signature for an element.
    Used to detect if sibling elements have similar structure.
    """
    if not isinstance(element, Tag):
        return None
    
    # Skip removed/hidden elements
    if element.name.lower() in REMOVE_TAGS:
        return None
    if element.get('hidden') is not None:
        return None
    style = element.get('style', '')
    if 'display:none' in style.replace(' ', '') or 'visibility:hidden' in style.replace(' ', ''):
        return None
    
    # Build signature from child tag structure
    child_tags = []
    for child in element.children:
        if isinstance(child, Tag) and child.name.lower() not in REMOVE_TAGS:
            child_tags.append(child.name.lower())
    
    # Include element's own tag and class hints
    classes = element.get('class', [])
    class_hint = None
    if classes:
        # Use first class as a hint (often indicates card type)
        class_hint = classes[0] if isinstance(classes, list) else classes.split()[0]
    
    return (element.name.lower(), class_hint, tuple(child_tags[:10]))  # Limit depth


def extract_cell_data(element, base_url: str = "") -> dict:
    """
    Extract structured data from an element for table conversion.
    Returns dict with detected fields.
    """
    data = {
        'texts': [],
        'links': [],
        'images': [],
        'percentages': [],
        'numbers': [],
        'dates': []
    }
    
    if not isinstance(element, Tag):
        return data
    
    # Extract all text segments
    for text_node in element.stripped_strings:
        text = text_node.strip()
        if not text:
            continue
            
        # Categorize the text
        if re.match(r'^\d{1,3}%$', text):
            data['percentages'].append(text)
        elif re.match(r'^[\d,]+(\.\d+)?$', text):
            data['numbers'].append(text)
        elif re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', text, re.I):
            data['dates'].append(text)
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', text):
            data['dates'].append(text)
        else:
            data['texts'].append(text)
    
    # Extract links
    for a in element.find_all('a', href=True):
        href = a.get('href', '')
        link_text = a.get_text(strip=True)
        if href and link_text:
            if base_url and not href.startswith(('http://', 'https://', 'mailto:', '#')):
                href = urljoin(base_url, href)
            data['links'].append({'text': link_text, 'url': href})
    
    # Extract images
    for img in element.find_all('img', src=True):
        src = img.get('src', '')
        alt = img.get('alt', '')
        if src:
            if base_url and not src.startswith(('http://', 'https://', 'data:')):
                src = urljoin(base_url, src)
            data['images'].append({'src': src, 'alt': alt})
    
    return data


def detect_repeated_pattern(element, base_url: str = "") -> str:
    """
    Detect if element contains repeated similar children and convert to table.
    Returns markdown table string if pattern detected, empty string otherwise.
    """
    if not ENABLE_PATTERN_DETECTION:
        return ""
    
    if not isinstance(element, Tag):
        return ""
    
    # Get direct children that are tags
    children = [c for c in element.children if isinstance(c, Tag)]
    if len(children) < MIN_PATTERN_SIBLINGS:
        return ""
    
    # Generate signatures for all children
    signatures = []
    for child in children:
        sig = get_element_signature(child)
        if sig:
            signatures.append((sig, child))
    
    if len(signatures) < MIN_PATTERN_SIBLINGS:
        return ""
    
    # Find the most common signature
    sig_counts = Counter(sig for sig, _ in signatures)
    most_common_sig, count = sig_counts.most_common(1)[0]
    
    # Need at least MIN_PATTERN_SIBLINGS with same signature
    if count < MIN_PATTERN_SIBLINGS:
        return ""
    
    # Check if this represents a significant portion (at least 50%)
    if count < len(signatures) * 0.5:
        return ""
    
    # Extract data from matching elements
    matching_elements = [child for sig, child in signatures if sig == most_common_sig]
    
    rows_data = []
    for elem in matching_elements:
        cell_data = extract_cell_data(elem, base_url)
        rows_data.append(cell_data)
    
    # Determine columns based on what data is present
    columns = []
    headers = []
    
    # Check what data types are consistently present
    has_percentages = all(len(r['percentages']) > 0 for r in rows_data)
    has_links = all(len(r['links']) > 0 for r in rows_data)
    has_dates = any(len(r['dates']) > 0 for r in rows_data)
    
    # Build column definitions
    if has_percentages:
        # Count how many percentage columns
        max_pct = max(len(r['percentages']) for r in rows_data)
        if max_pct == 1:
            columns.append(('percentages', 0, 'Score'))
            headers.append('Score')
        elif max_pct == 2:
            columns.append(('percentages', 0, 'Rating 1'))
            columns.append(('percentages', 1, 'Rating 2'))
            headers.extend(['Rating 1', 'Rating 2'])
        else:
            for i in range(min(max_pct, 3)):
                columns.append(('percentages', i, f'Score {i+1}'))
                headers.append(f'Score {i+1}')
    
    if has_links:
        columns.append(('links', 0, 'Name'))
        headers.append('Name')
    
    if has_dates:
        columns.append(('dates', 0, 'Date'))
        headers.append('Date')
    
    # If no structured columns found, fall back to text
    if not columns:
        columns.append(('texts', 0, 'Item'))
        headers.append('Item')
    
    # Build table rows
    table_rows = []
    for row_data in rows_data:
        row = []
        for col_type, col_idx, _ in columns:
            if col_type == 'links' and col_idx < len(row_data['links']):
                link = row_data['links'][col_idx]
                row.append(f"[{link['text']}]({link['url']})")
            elif col_type == 'percentages' and col_idx < len(row_data['percentages']):
                row.append(row_data['percentages'][col_idx])
            elif col_type == 'dates' and col_idx < len(row_data['dates']):
                row.append(row_data['dates'][col_idx])
            elif col_type == 'texts' and col_idx < len(row_data['texts']):
                row.append(row_data['texts'][col_idx])
            elif col_type == 'numbers' and col_idx < len(row_data['numbers']):
                row.append(row_data['numbers'][col_idx])
            else:
                row.append('—')
        
        if any(cell != '—' for cell in row):
            table_rows.append(row)
    
    if len(table_rows) < MIN_PATTERN_SIBLINGS:
        return ""
    
    # Generate markdown table
    lines = []
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
    for row in table_rows:
        # Escape pipe characters in cell content
        escaped_row = [cell.replace('|', '\\|') for cell in row]
        lines.append('| ' + ' | '.join(escaped_row) + ' |')
    
    return "\n\n" + '\n'.join(lines) + "\n\n"


def extract_text_with_structure(element, base_url: str = "", check_patterns: bool = True) -> str:
    """
    Recursively extract text from HTML element, preserving structure.
    Returns markdown-formatted text.
    """
    if element is None:
        return ""
    
    if isinstance(element, Comment):
        return ""
    
    if isinstance(element, NavigableString):
        text = str(element)
        text = re.sub(r'\s+', ' ', text)
        return text
    
    tag_name = element.name.lower() if element.name else ""
    
    if tag_name in REMOVE_TAGS:
        return ""
    
    if element.get('hidden') is not None:
        return ""
    style = element.get('style', '')
    if 'display:none' in style.replace(' ', '') or 'visibility:hidden' in style.replace(' ', ''):
        return ""
    
    # Check for repeated patterns in container elements
    if check_patterns and tag_name in ('div', 'section', 'main', 'article', 'ul', 'ol', 'tbody'):
        pattern_table = detect_repeated_pattern(element, base_url)
        if pattern_table:
            return pattern_table
    
    # Process children
    children_text = []
    for child in element.children:
        child_text = extract_text_with_structure(child, base_url, check_patterns)
        if child_text:
            children_text.append(child_text)
    
    content = ''.join(children_text)
    
    # Apply formatting based on tag
    if tag_name in HEADING_TAGS:
        level = int(tag_name[1])
        prefix = '#' * level
        content = clean_text(content).strip()
        if content:
            return f"\n\n{prefix} {content}\n\n"
        return ""
    
    elif tag_name == 'p':
        content = clean_text(content).strip()
        if content:
            return f"\n\n{content}\n\n"
        return ""
    
    elif tag_name == 'br':
        return "\n"
    
    elif tag_name == 'hr':
        return "\n\n---\n\n"
    
    elif tag_name in ('strong', 'b'):
        content = content.strip()
        if content:
            return f"**{content}**"
        return ""
    
    elif tag_name in ('em', 'i'):
        content = content.strip()
        if content:
            return f"*{content}*"
        return ""
    
    elif tag_name == 'code':
        content = content.strip()
        if content:
            return f"`{content}`"
        return ""
    
    elif tag_name == 'pre':
        content = element.get_text()
        if content.strip():
            return f"\n\n```\n{content.strip()}\n```\n\n"
        return ""
    
    elif tag_name == 'blockquote':
        content = clean_text(content).strip()
        if content:
            quoted = '\n'.join(f"> {line}" for line in content.split('\n'))
            return f"\n\n{quoted}\n\n"
        return ""
    
    elif tag_name == 'a':
        href = element.get('href', '')
        content = content.strip()
        if content and href:
            if base_url and not href.startswith(('http://', 'https://', 'mailto:', '#')):
                href = urljoin(base_url, href)
            return f"[{content}]({href})"
        return content
    
    elif tag_name == 'img':
        alt = element.get('alt', '')
        src = element.get('src', '')
        if src:
            if base_url and not src.startswith(('http://', 'https://', 'data:')):
                src = urljoin(base_url, src)
            return f"![{alt}]({src})"
        return ""
    
    elif tag_name == 'ul':
        items = []
        for li in element.find_all('li', recursive=False):
            item_text = extract_text_with_structure(li, base_url, check_patterns=False)
            item_text = clean_text(item_text).strip()
            if item_text:
                lines = item_text.split('\n')
                formatted = [f"- {lines[0]}"]
                for line in lines[1:]:
                    if line.strip():
                        formatted.append(f"  {line}")
                items.append('\n'.join(formatted))
        if items:
            return "\n\n" + '\n'.join(items) + "\n\n"
        return ""
    
    elif tag_name == 'ol':
        items = []
        for idx, li in enumerate(element.find_all('li', recursive=False), 1):
            item_text = extract_text_with_structure(li, base_url, check_patterns=False)
            item_text = clean_text(item_text).strip()
            if item_text:
                lines = item_text.split('\n')
                formatted = [f"{idx}. {lines[0]}"]
                for line in lines[1:]:
                    if line.strip():
                        formatted.append(f"   {line}")
                items.append('\n'.join(formatted))
        if items:
            return "\n\n" + '\n'.join(items) + "\n\n"
        return ""
    
    elif tag_name == 'li':
        return content
    
    elif tag_name == 'table':
        return convert_table(element)
    
    elif tag_name in BLOCK_TAGS:
        content = clean_text(content).strip()
        if content:
            return f"\n\n{content}\n\n"
        return ""
    
    return content


def convert_table(table_element) -> str:
    """Convert HTML table to markdown table."""
    rows = []
    
    for tr in table_element.find_all('tr'):
        cells = []
        for cell in tr.find_all(['th', 'td']):
            cell_text = cell.get_text(separator=' ', strip=True)
            cell_text = re.sub(r'\s+', ' ', cell_text)
            cells.append(cell_text)
        if cells:
            rows.append(cells)
    
    if not rows:
        return ""
    
    max_cols = max(len(row) for row in rows)
    
    for row in rows:
        while len(row) < max_cols:
            row.append('')
    
    lines = []
    lines.append('| ' + ' | '.join(rows[0]) + ' |')
    lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
    
    for row in rows[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    
    return "\n\n" + '\n'.join(lines) + "\n\n"


def html_to_markdown(html: str, base_url: str = "", detect_patterns: bool = True) -> str:
    """
    Convert HTML to clean markdown.
    
    Args:
        html: HTML content string
        base_url: Base URL for resolving relative links
        detect_patterns: Enable pattern detection for auto-table conversion
        
    Returns:
        Clean markdown string
    """
    global ENABLE_PATTERN_DETECTION
    ENABLE_PATTERN_DETECTION = detect_patterns
    
    soup = BeautifulSoup(html, 'html.parser')
    
    main_content = (
        soup.find('main') or 
        soup.find('article') or 
        soup.find(id='content') or
        soup.find(class_='content') or
        soup.find('body') or
        soup
    )
    
    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    markdown = extract_text_with_structure(main_content, base_url)
    
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()
    
    if title and not markdown.startswith(f"# {title}"):
        markdown = f"# {title}\n\n{markdown}"
    
    return markdown


def url_to_markdown(url: str, timeout: int = 30, detect_patterns: bool = True) -> str:
    """
    Fetch URL and convert to markdown.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        detect_patterns: Enable pattern detection for auto-table conversion
        
    Returns:
        Markdown string
    """
    html = fetch_url(url, timeout)
    return html_to_markdown(html, base_url=url, detect_patterns=detect_patterns)


def main():
    parser = argparse.ArgumentParser(
        description='Convert web page to clean markdown'
    )
    parser.add_argument('url', help='URL to convert')
    parser.add_argument('output', nargs='?', help='Output file (optional, prints to stdout if omitted)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--no-tables', action='store_true', 
                        help='Disable pattern detection (no auto-table conversion)')
    
    args = parser.parse_args()
    
    try:
        markdown = url_to_markdown(
            args.url, 
            args.timeout, 
            detect_patterns=not args.no_tables
        )
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"✅ Saved to {args.output}")
        else:
            print(markdown)
            
    except requests.RequestException as e:
        print(f"❌ Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
