#!/usr/bin/env python3

import json
import os
import re
import sys
import argparse
from typing import Any
from bs4 import BeautifulSoup
import unicodedata

#Clean HTML Logic out of rendered content
def clean_rendered_content(content: str) -> str:
    """
    Parses HTML, extracts text from header (h1–h6) and paragraph (p) tags,
    strips control‑category Unicode chars plus \n, \r, and \t,
    and returns an HTML-like string where headings retain their tags
    and paragraphs are plain text lines.
    """
    soup = BeautifulSoup(content, 'html.parser')
    
    elements = soup.find_all(['h1','h2','h3','h4','h5','h6','p'])
    cleaned_blocks = []
    
    for el in elements:
        # Extract visible text
        text = el.get_text(separator=' ', strip=True)
        # Remove control chars and explicit newline/tab/carriage returns
        clean = ''.join(
            ch for ch in text
            if not unicodedata.category(ch).startswith('C')
               and ch not in ('\n', '\r', '\t')
        )
        if not clean:
            continue
        
        # Wrap headings in their tag; paragraphs as plain text
        if el.name in ['h1','h2','h3','h4','h5','h6']:
            cleaned_blocks.append(f"<{el.name}>{clean}</{el.name}>")
        else:  # paragraph
            cleaned_blocks.append(clean)
    
    # Join with newline for readability
    return " ".join(cleaned_blocks)

def build_tree(input_path: str, output_path: str) -> None:
    """
    Builds a hierarchical tree structure from a flat list of JSON items with parent-child relationships.

    Args:
        input_path (str): Path to the input JSON file containing the flat list of items.
        output_path (str): Path to the output JSON file to write the tree structure.
    """
    # Load raw data from JSON file
    with open(input_path, 'r', encoding='utf-8') as file:
        items: list[dict[str, Any]] = json.load(file, strict=False) #Hack - fix later

    print("length of items: ", len(items))
    # Create a dictionary of simplified nodes indexed by their ID
    nodes: dict[int, dict[str, Any]] = {}
    empty_pages: dict[int, str] = {}
    empty_pages_count = 0
    special_pages: dict[int, str] = {}
    special_pages_count = 0

    for item in items:
        rendered_content = item.get('content', {}).get('rendered', '') 
        if not rendered_content:
            content = "Page is empty. Check again later..."
            empty_pages[item['id']] = item['link']
            empty_pages_count += 1
        else:
            content = clean_rendered_content(rendered_content)
            if not content:
                content = "Does not have paragraph tags <p></p>. This is a special page (ie. contains only hyperlinks, special paragraph tags like excerpts, etc). Manually add content."
                special_pages[item['id']] = item['link']
                special_pages_count += 1

        node = {
            'id': item['id'],
            'title': item.get('title', {}).get('rendered', ''),
            'link': item['link'],
            'content': content,
            'modified': item['modified'],
            'slug': item['slug'],
            'status': item['status'],
            'excerpt': item.get('excerpt', {}).get('rendered', ''),
            'children': []
        }
        nodes[item['id']] = node

    # Construct tree by assigning children to their respective parent nodes
    output_data = {
        "empty_pages_count": empty_pages_count,
        "empty_pages": empty_pages,
        "special_pages_count": special_pages_count,
        "special_pages": special_pages,
        "webpage_tree": [],                           # will hold the actual page nodes
    }

    # Populate the tree
    for item in items:
        node = nodes[item['id']]
        parent_id = item.get('parent', 0) or 0
        if parent_id in nodes:
            nodes[parent_id]['children'].append(node)
        else:
            output_data["webpage_tree"].append(node)

    # Write the structured dict to the output file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=2)


#!/usr/bin/env python3
import argparse
import os
import re
from typing import Generator

def gather_inputs(inputs: list[str]) -> Generator[str, None, None]:
    """
    Given a list of paths, yield every JSON file path.
    If the path is a file, yield it.
    If it’s a directory, walk it recursively and yield any .json files.
    """
    for path in inputs:
        if os.path.isdir(path):
            # walk the directory tree
            for root, dirs, files in os.walk(path):
                for name in files:
                    if name.lower().endswith('.json'):
                        yield os.path.join(root, name)
        else:
            # assume it’s a file
            yield path

def main():
    parser = argparse.ArgumentParser(
        description="Index one or more WP endpoint JSON files or directories."
    )
    parser.add_argument(
        'inputs',
        nargs='+',
        help='Paths to JSON files or directories containing JSON dumps'
    )
    parser.add_argument(
        '-o','--output-dir',
        default="output/website-data/indexed-website-data",
        help='Directory to write the indexed JSON files into'
    )
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)

    # Instead of looping directly over args.inputs,
    # we first expand directories into their .json files:
    for input_path in gather_inputs(args.inputs):
        base = os.path.basename(input_path)
        name, _ = os.path.splitext(base)
        endpoint = re.sub(r'_endpoint_content$', '', name)
        output_name = f"indexed_{endpoint}_data.json"
        output_path = os.path.join(args.output_dir, output_name)

        print(f"Processing {input_path!r} → {output_path!r}")
        build_tree(input_path, output_path)

if __name__ == '__main__':
    main()