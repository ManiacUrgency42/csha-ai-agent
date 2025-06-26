import os
import json
import time
import pickle
from typing import Any, List, Dict

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from rank_bm25 import BM25Okapi

# Ensure required NLTK data is available
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

# Load English stopwords
stop_words: set[str] = set(stopwords.words('english'))

# Determine paths for input and output files
current_dir: str = os.path.dirname(os.path.realpath(__file__))
input_file_path: str = os.path.join(current_dir, "output/structured_text.json")
index_output_path: str = os.path.join(current_dir, "output/document_index.pkl")

# Load structured document data from JSON
print(f"Loading documents from {input_file_path}")
document_data: Dict[str, Any]
with open(input_file_path, 'r', encoding='utf-8') as json_file:
    document_data = json.load(json_file)

# Tokenize headings and subheadings into a list of token lists
tokenized_documents: List[List[str]] = []
for heading in document_data.get("headings", []):
    title_text = heading.get("heading_title", "").strip()
    if title_text.lower() == "sources":
        continue

    body_text = heading.get("text", "").strip()
    if body_text:
        tokenized_documents.append(word_tokenize(body_text))

    for subheading in heading.get("subheadings", []):
        sub_text = subheading.get("text", "").strip()
        if sub_text:
            tokenized_documents.append(word_tokenize(sub_text))

print(f"Number of tokenized document segments: {len(tokenized_documents)}")

# Backup existing BM25 index file if present
if os.path.exists(index_output_path):
    backup_path = f"{index_output_path}.previous-version"
    os.rename(index_output_path, backup_path)
    print(f"Existing index backed up to: {backup_path}")

# Create and save the BM25 index
print("Creating BM25 index...")
start_time: float = time.time()
bm25_index = BM25Okapi(tokenized_documents)
indexing_duration: float = time.time() - start_time

with open(index_output_path, 'wb') as output_file:
    pickle.dump(bm25_index, output_file)

print(f"Indexing completed in {indexing_duration:.4f} seconds")
