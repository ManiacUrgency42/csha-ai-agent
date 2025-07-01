# CSHA AI Agent

![Static Badge](https://img.shields.io/badge/python_version-3.9.6-blue)

## Table of Contents

- [About](#about)
- [RAG Architecture](#rag-architecture)
- [Installation and Usage](#installation-and-usage)
  - [Dependencies](#dependencies)
  - [Environment Variables](#environment-variables)
  - [Run the Agent](#run-the-agent)
- [Known Issues](#known-issues)
  
## About

This project provides a simple AI agent with a CLI chat interface that answers questions about the [*Attracting and Retaining Adolescent Patients* PDF](https://drive.google.com/drive/folders/1Kgctv62f9WrOI9ZydvRtXTjeoLObhkcO) supplied by the California School‑Based Health Alliance (CSHA), a non‑profit organization. The agent is built on a Retrieval‑Augmented Generation (RAG) framework.

## RAG Architecture

![RAG architecture](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/rag_based_system_architecture.png)

## Backend

### Data Processing

Parsers and Indexers work together closely and can often be combined into one Python file.

#### Parsers

Parsers extract text and metadata from data formats such as PDF, images, tables, and charts. Choosing a parsing tool depends on the data format and the complexity of the data (i.e., does the data format contain large tables, pie-charts, mathematical formulas that need to be extracted?).

#### <u>Example</u>

Standard-format PDFs can be handled with rule-based tools such as PDFminer.six, while unstructured PDFs—where text appears in tables or images—often require ML-based tools like PaddleOCR. ML approaches are more robust but demand greater setup effort and expertise compared to simpler methods.

### Indexers

Indexers take the extracted text and its metadata, then organize the data into a format such as JSON.

##### <u>Example</u>

We first identify headings in the PDF—either by looking at their on-page positions (coordinates) or by using an ML model trained to recognize header text. Once we know each section and subsection heading, we split the document into text chunks based on those headings. Finally, we nest those chunks in a hierarchical structure so that every paragraph is stored under the correct section or subsection. This ensures that the text is chunked and stored logically to improve retrieval performance.

```json
[Insert a JSON snippet]
```

### Vector Embedder

Vector embeddings are fixed-length arrays of numbers that capture the semantic meaning of text (words, sentences, paragraphs).

#### Embedding Model

An embedding model creates vector embeddings. We then store these vector embeddings into a Vector Database for retrieval later on.

We are currently using OpenAI’s embedding model: `text-embedding-large-3`.

#### Vector Database

A Vector Database is a specialized database that has built-in mathematical functions for storing and manipulating vector embeddings in a high-dimensional space.

We are currently using `Pinecone Vector Database` because of the easy setup and developer-friendly documentation.

Before the vectors are upserted to Pinecone VDB, a unique “id” key for each text chunk is generated. This “id” key gets stored in the text chunk’s JSON object and the corresponding text embedding, so during the retrieval process the key is returned, and used to map to the text chunk. (This is explained in more detail in the Retrieval section.)

### Bm25 Tokenizer

Okapi BM25 Retrieval is a keyword-based document retriever that improves on the Term Frequency-Inverse Document Frequency (TF-IDF) ranking algorithm. Term Frequency is the raw count of how many times word *t* appears in document *d*. Inverse Document Frequency is the number of documents *N* divided by the number of documents in which term *t* appears at least once *n<sub>t</sub>*. Therefore, more frequent words such as “the”, “and”, and “is” get less weight. The score of the document is calculated by multiplying TF by IDF.

Given a query **Q**, containing keywords *q₁,…,qₙ*, the BM25 score of a document **D** is:

- **score(D, Q)**: The total BM25 score of document D for query Q.
- **D**: The document being scored.
- **Q**: The query, viewed as a sequence of terms (q₁, q₂, …, qₙ).
- **n**: The number of terms in the query Q.
- **i**: The index of the current query term (1 through n).
- **qᵢ**: The i-th term in the query.
- **IDF(qᵢ)**: Inverse document frequency of qᵢ (down-weights common terms).
- **f(qᵢ, D)**: The raw count of how many times qᵢ appears in D.
- **k₁**: TF-saturation parameter (≥ 0) that controls how quickly term frequency plateaus.
- **b**: Length-normalization parameter (0 ≤ b ≤ 1) that adjusts for document length.
- **|D|**: The length of document D (e.g., word count).
- **avgdl**: The average document length across the corpus (same units as |D|).

#### Why BM25 instead of TF-IDF?

BM25 adds two parameters.

##### TF Saturation (parameter k₁)

Instead of letting TF grow linearly, BM25 transforms it so that as a term’s count increases, its incremental impact tapers off around k₁ + 1.

##### Length Normalization (parameter b)

Adjusts for document length by computing normalization where |*d*| is the length of document *d* and *avgdl* is the average document length. Terms in longer documents get down-weighted, and those in shorter documents get up-weighted, controlled by *b*.

### NLTK Tokenizer

The NLTK Tokenizer splits the text document into tokens that are the size of a word or part of a word. These tokenized documents are then stored in the Pickle index.

### Pickle Index

Pickle is a Python module that implements binary protocols for serializing and deserializing a Python object structure. Pickle is used instead of JSON because it can store complex Python objects like NumPy arrays and offers faster read/write operations due to its compact binary format. This enables lower-latency BM25 retrieval.

> **Note:** If we have too many documents, we can consider scaling to a production database that supports BM25 retrieval.

## Retrieval

When a user submits a query to the chat interface, the system augments the prompt with relevant content using one of two retrieval methods: vector-based retrieval or BM25 keyword retrieval. Our code organizes the retrieval logic into a modular function, so you can easily switch between vector retrieval and BM25 retrieval as needed.

> **Note:** Choosing the best retrieval strategy is an ongoing research effort, as there are numerous retrieval techniques to explore—hybrid approaches, which blend the semantic power of vector embeddings with the precision of BM25 keyword scoring, are just one example.

### Vector Retriever

#### Embedding Model

When the user feeds in their query, the input needs to be converted to a vector so that it can be compared with the vectors in the Pinecone VDB. The same Embedding Model used to create vector embeddings for the processed documents is used for the user queries.

#### Similarity Comparison Method

To retrieve the most relevant documents from Pinecone VDB we use semantic similarity, measuring how closely related two data points are in meaning or context. There are many semantic similarity metrics including cosine similarity and Euclidean distance. This script uses cosine similarity because it is not affected by the magnitude of the vectors (which can represent the text length or word frequency).

### Bm25 Retriever

#### NER Keyword Expander

The NER (Named Entity Recognition) Keyword Expander is a call to an LLM to help expand named entities (names, organizations, events, and locations) in the user query to improve keyword retrieval. The NER Keyword Expander also fixes spelling errors and removes stop-words such as “like”, “and”, and “is”.

##### <u>Example</u>

**Input**
```
What is the name of the most famous speech by MLK?
```
**Output**
```
name, famous, speech, MLK, title, designation, well-known, renowned, address, talk, Martin Luther King, Martin Luther King, Jr.
```

#### Rank BM25

Uses Okapi BM25 to retrieve the top “k” most relevant document “id” keys.

## Prompt Augmentation

### Prompt Templates

We leverage LangChain’s prompt templates to assemble the messages sent to the language model. These templates are both modular and reusable, so you can dynamically switch to a new prompt template, insert the user’s query, and any contextual information before invoking the LLM for the final response.
The prompt template we used is called `MULTIPLE_REFERENCES_RESPONSE_TEMPLATE`. This template instructs the LLM to cite the documents it used in the response.

> **Note:** Context engineering techniques such as defining the system role, adding delimiters, and providing example I/Os were used to improve the LLM’s response. Better context engineering lets less powerful, lower-cost models match the performance of more expensive ones.

## Generation

### Models

Large language models (LLMs) serve as another modular component in our system. Choosing a proprietary LLM lets you skip managing hosting infrastructure and inference costs, since the provider handles all of that. Popular options include OpenAI, Anthropic, and Google.

We are using OpenAI’s `gpt-4.1`, the most intelligent but expensive OpenAI frontier model.

> **Note:** Choosing the optimal LLM is a research task that requires understanding the cost-intelligence trade-off for specific tasks.

## Installation and Usage

```
pip3 install -r requirements.txt
```

### Dependencies

- `requests` – fetch data from the web
- `pdfminer.six` – parse PDFs
- `nltk` – tokenize text
- `rank_bm25` – BM25 retrieval
- `pinecone` – interface with the Pinecone vector database
- `langchain` – core LangChain tools (e.g., prompt templates)
- `langchain-openai` – LangChain integrations with OpenAI models
- `langchain-pinecone` – LangChain integrations with Pinecone (e.g., `PineconeVectorStore`)

### Environment Variables

**Good news — you don’t need to create Pinecone or OpenAI accounts.**  
Project‑scoped API keys are already provided for testing; you only have to set them in your shell (or a `.env` file) before running the scripts.

<details>
<summary><strong>Quick setup for macOS / Linux (bash/zsh)</strong></summary>

```bash
export PINECONE_API_KEY="pcsk_3c1tKo_QmNHRR9YXWiqXwD6dPdYPhPAgquiu7utSpfUaBu9mMqkgNnSQQT7rYdhKBTSrkx"
export OPENAI_API_EMBEDDINGS_KEY="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"
export OPENAI_API_QUERY_KEY="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"
```
</details>

<details>
<summary><strong>Quick setup for Windows (PowerShell)</strong></summary>

```powershell
setx PINECONE_API_KEY "pcsk_3c1tKo_QmNHRR9YXWiqXwD6dPdYPhPAgquiu7utSpfUaBu9mMqkgNnSQQT7rYdhKBTSrkx"
setx OPENAI_API_EMBEDDINGS_KEY "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"
setx OPENAI_API_QUERY_KEY "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"
```
</details>

**Prefer a `.env` file?** Create one in the project root:

```env
PINECONE_API_KEY=pcsk_3c1tKo_QmNHRR9YXWiqXwD6dPdYPhPAgquiu7utSpfUaBu9mMqkgNnSQQT7rYdhKBTSrkx
OPENAI_API_EMBEDDINGS_KEY=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
OPENAI_API_QUERY_KEY=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
```

### Run the Agent

You can download the *Attracting and Retaining Adolescent Patients* PDF here (if you want to test `pdf_parser_indexer.py`): https://drive.google.com/drive/folders/1Kgctv62f9WrOI9ZydvRtXTjeoLObhkcO

**To chat with the AI agent, run the following scripts from the command line:**

```
python3 bm25_tokenizer.py
```

```
python3 vector_embedder.py
```

```
python3 user_query_document.py
```

## Known Issues

- `pdf_parser_indexer.py` does not reliably extract text from the PDF or index chunks by heading and subheading because of one-off edge cases, so some manual editing was required to create `structured_text.json`. This JSON file is used for the vector embedder and BM25 tokenizer. A future upgrade is to use a more robust ML-based PDF parser—though we’ll need to weigh the accuracy gains against added development time.
