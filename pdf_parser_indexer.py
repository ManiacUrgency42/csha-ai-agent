import json
from typing import Any, Dict, List, Tuple
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LTTextLineHorizontal, LTChar


def extract_text_with_attributes(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts each character from the PDF along with its layout attributes.
    Skips rotated text lines for clarity.
    """
    text_elements: List[Dict[str, Any]] = []

    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextBoxHorizontal):
                for text_line in element:
                    if isinstance(text_line, LTTextLineHorizontal):
                        # Skip rotated lines
                        if any(abs(round(char.matrix[1])) != 0 for char in text_line if isinstance(char, LTChar)):
                            continue

                        for char in text_line:
                            if isinstance(char, LTChar):
                                text_elements.append({
                                    "text": char.get_text(),
                                    "font_size": char.size,
                                    "fontname": char.fontname,
                                    "x0": char.x0,
                                    "x1": char.x1,
                                    "y0": char.y0,
                                    "y1": char.y1,
                                })

    # Persist raw character data
    with open("output/text_elements.json", "w", encoding="utf-8") as file:
        json.dump(text_elements, file, ensure_ascii=False, indent=2)

    return text_elements


def determine_common_text_attributes(
    text_elements: List[Dict[str, Any]]
) -> Tuple[float, str]:
    """
    Identifies the most frequent font size and font name in the extracted elements.
    """
    font_size_counts: Dict[float, int] = {}
    font_name_counts: Dict[str, int] = {}

    for element in text_elements:
        size = element.get("font_size")
        name = element.get("fontname")
        if size is not None:
            font_size_counts[round(size, 1)] = font_size_counts.get(round(size, 1), 0) + 1
        if name:
            font_name_counts[name] = font_name_counts.get(name, 0) + 1

    # Determine most common attributes
    common_size = max(font_size_counts, key=font_size_counts.get)
    common_name = max(font_name_counts, key=font_name_counts.get)

    return common_size, common_name


def save_text_elements_to_json(
    text_elements: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """
    Structures extracted character data into parts, subheadings, and body text
    based on font runs. Outputs a nested JSON of headings and associated text.
    """
    data: Dict[str, Any] = {"headings": []}

    # Body text criteria
    body_fonts = {"KECEOE+ArialMT", "IJBNMI+Arial-ItalicMT"}
    body_font_size = 10.0

    def detect_runs(
        elements: List[Dict[str, Any]],
        target_font: str = None,
        target_size: float = None,
    ) -> List[Tuple[int, int]]:
        """
        Finds contiguous runs of elements matching font and size on the same baseline.
        Returns list of (start_index, end_index) tuples.
        """
        runs: List[Tuple[int, int]] = []
        start_index: int = None  # type: ignore
        prev_y: float = None  # type: ignore

        for idx, element in enumerate(elements):
            font = element.get("fontname")
            size = round(element.get("font_size", 0), 1)
            y_pos = round(element.get("y1", 0), 1)
            matches_font = (target_font is None or font == target_font)
            matches_size = (target_size is None or size == target_size)

            if matches_font and matches_size:
                # Start of a new run if baseline changes
                if start_index is None or y_pos != prev_y:
                    start_index = idx
                prev_y = y_pos
            else:
                if start_index is not None:
                    runs.append((start_index, idx))
                    start_index = None
                    prev_y = None

        if start_index is not None:
            runs.append((start_index, len(elements)))

        return runs

    # Identify part headings (font size 12)
    heading_runs = detect_runs(text_elements, target_size=12)
    for part_idx, (heading_start_idx, heading_end_idx) in enumerate(heading_runs):
        part_title = ''.join(
            el['text'] for el in text_elements[heading_start_idx:heading_end_idx]
        ).strip()
        data['headings'].append({
            'part_number': part_idx + 1,
            'part_title': part_title,
            'text': '',
            'subheadings': []
        })

    # Identify subheadings (bold italic Arial, size 10)
    subheading_runs = detect_runs(
        text_elements,
        target_font="SDBVWO+Arial-BoldItalicMT",
        target_size=10,
    )

    # Assign subheadings under corresponding parts
    for sub_start_idx, sub_end_idx in subheading_runs:
        # Find parent part index
        parent_part = None
        for idx, (part_start, _) in enumerate(heading_runs):
            if part_start <= sub_start_idx:
                parent_part = idx
            else:
                break
        if parent_part is None:
            continue

        sub_title = ''.join(
            el['text'] for el in text_elements[sub_start_idx:sub_end_idx]
        ).strip()

        # Determine slice end: next subheading or next heading
        next_boundary = len(text_elements)
        for next_sub, _ in subheading_runs:
            if next_sub > sub_start_idx:
                next_boundary = min(next_boundary, next_sub)
                break
        for next_head, _ in heading_runs:
            if next_head > sub_start_idx:
                next_boundary = min(next_boundary, next_head)
                break

        content_slice = text_elements[sub_end_idx:next_boundary]
        filtered_text = ''.join(
            w['text'] for w in content_slice
            if w.get('fontname') in body_fonts and round(w.get('font_size', 0),1) == body_font_size
        ).strip()

        data['headings'][parent_part]['subheadings'].append({
            'subheading_number': len(data['headings'][parent_part]['subheadings']) + 1,
            'subheading_title': sub_title,
            'text': filtered_text
        })

    # Extract body text under each part (before its first subheading)
    for idx, (part_start, part_end) in enumerate(heading_runs):
        # Determine text region for body
        next_part_start = heading_runs[idx+1][0] if idx + 1 < len(heading_runs) else len(text_elements)
        first_sub_start = None
        for sub_start, _ in subheading_runs:
            if part_start < sub_start < next_part_start:
                first_sub_start = sub_start
                break

        body_end_idx = first_sub_start if first_sub_start is not None else next_part_start
        body_slice = text_elements[part_end:body_end_idx]
        filtered_body = ''.join(
            w['text'] for w in body_slice
            if w.get('fontname') in body_fonts and round(w.get('font_size',0),1) == body_font_size
        ).strip()

        data['headings'][idx]['text'] = filtered_body

    # Write structured JSON
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    """Entry point for PDF parsing and structuring."""
    pdf_file = "attracting_and_retaining_adolescent_patients.pdf"
    structured_output = "output/structured_text.json"

    characters = extract_text_with_attributes(pdf_file)
    save_text_elements_to_json(characters, structured_output)

    print(f"Structured text data written to {structured_output}")


if __name__ == "__main__":
    main()
