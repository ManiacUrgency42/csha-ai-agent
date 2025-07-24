#!/usr/bin/env python3

import json
import os
import re
import sys
import argparse
from typing import Any

#Clean HTML Logic out of rendered content
def clean_rendered_content(content: str) -> str:
    cleaned_content = ""
    has_seen_anchor_tag = False
    has_seen_paragraph_tag = False
    i = 0
    while i < len(content):
        if has_seen_paragraph_tag:
            p = i + 2
            #paragraph_content = ""
            while content[p:p+4] != "</p>":
                #paragraph_content += content[p]
                if content[p:p+2] == "<a" or content[p:p+7] == "<a href":
                    has_seen_anchor_tag = True
                
                if has_seen_anchor_tag:
                    a = p
                    anchor_content = ""
                    while content[a:a+4] != "</a>":
                        anchor_content += content[a]
                        a += 1

                    has_seen_anchor_tag = False
                    cleaned_content += content[p]
                #     print("skipped content: ", content[p:p+((a+4)-p)])
                #     print("content[p+((a+4)-p)]: ", p+((a+4)-p))
                #     p += (a + 4) - p
                #     print("content[p]: ", content[p])
                #     cleaned_content += content[p]
                    print("\nAnchor Content:\n", anchor_content)
                # try:
                #     cleaned_content += content[p]
                # except IndexError:
                #     print(f"⚠️ IndexError at p={p} where content[p-2:p] = {content[p-2:p]}")
                #     print("Debugging message:", content[max(p-20, 0):min(p+20, len(content))])
                #     break 
                p += 1

            has_seen_paragraph_tag = False    
            i += p - i
            # print("\nParagraph Content:\n", paragraph_content)

        if has_seen_anchor_tag:
            a = i
            anchor_content = ""
            while content[a:a+4] != "</a>":
                anchor_content += content[a]
                a += 1

            has_seen_anchor_tag = False
            i += (a + 4) - i 
            # print("\nAnchor Content:\n", anchor_content)

        if content[i:i+3] == "<p>":
            # print("\nDiscovered Paragraph Tag\n")
            has_seen_paragraph_tag = True
        elif content[i:i+2] == "<a" or content[i:i+7] == "<a href":
            # print("\nDiscovered Anchor Tag\n")
            has_seen_anchor_tag = True
        
        i += 1

    return cleaned_content     

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
