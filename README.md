![Header](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/github-header-image.png)

![Static Badge](https://img.shields.io/badge/python_version-3.9.6-blue)

# Table of Contents

- [About](#about)
- [RAG Architecture](#rag-architecture)
- [Installation and Usage](#installation-and-usage)
  - [Dependencies](#dependencies)
  - [Environment Variables](#environment-variables)
  - [Run the Agent](#run-the-agent)
- [Known Issues](#known-issues)
  
# About

This project provides a simple AI agent with a CLI chat interface that answers questions about the [*Attracting and Retaining Adolescent Patients* PDF](https://drive.google.com/drive/folders/1Kgctv62f9WrOI9ZydvRtXTjeoLObhkcO) supplied by the California School‑Based Health Alliance (CSHA), a non‑profit organization. The agent is built on a Retrieval‑Augmented Generation (RAG) framework.

# RAG Architecture

![RAG architecture](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/rag_based_system_architecture.png)

## Components

- [1 Backend](#1-backend)
  - [1.1 Data Processing](#11-data-processing)
    - [1.1.1 Parsers](#111-parsers)
    - [1.1.2 Indexers](#112-indexers)
  - [1.2 Vector Embedder](#12-vector-embedder)
    - [1.2.1 Embedding Model](#121-embedding-model)
    - [1.2.2 Vector Database](#122-vector-database)
  - [1.3 BM25 Tokenizer](#13-bm25-tokenizer)
    - [1.3.1 Why BM25 instead of TF-IDF?](#131-why-bm25-instead-of-tf-idf)
    - [1.3.2 NLTK Tokenizer](#132-nltk-tokenizer)
    - [1.3.3 Pickle Index](#133-pickle-index)
- [2 Retrieval](#2-retrieval)
  - [2.1 Vector Retriever](#21-vector-retriever)
    - [2.1.1 Embedding Model](#211-embedding-model)
    - [2.1.2 Similarity Comparison Method](#212-similarity-comparison-method)
  - [2.2 BM25 Retriever](#22-bm25-retriever)
    - [2.2.1 NER Keyword Expander](#221-ner-keyword-expander)
    - [2.2.2 Rank BM25](#222-rank-bm25)
- [3 Prompt Augmentation](#3-prompt-augmentation)
  - [3.1 Prompt Templates](#31-prompt-templates)
- [4 Generation](#4-generation)
  - [4.1 Models](#41-models)

## What is LangChain?

[LangChain](https://python.langchain.com/docs/introduction/) is a Python framework that lets you build LLM-powered applications by wiring together a set of modular components. For example:

- PromptTemplates: define reusable, fill-in-the-blank prompts so you never hand-craft raw strings.

- Chains: sequence one or more steps (LLM calls, data transforms, retrievals, etc.) into a single pipeline.

- Retrievers: handle semantic lookup of relevant text chunks via embeddings, so your model only sees what matters.

- Memory: maintain and recall conversational or application state across calls.

## 1 Backend

The backend handles data processing and storage. When working with large-scale data, organizing it logically in a data store can significantly improve retrieval accuracy and reduce latency. For vector retrieval, logically organizing data into well-structured chunks with metadata allows for more accurate embeddings, efficient ID-to-text mapping, and fast metadata filtering. For BM25 keyword retrieval, breaking text into logical chunks ensures that word counts are calculated within the correct context, which improves match quality, and makes it faster to search only the most relevant parts of the data.

### 1.1 Data Processing

Parsers and Indexers work together closely and can often be combined into one Python file.

#### 1.1.1 Parsers

Parsers extract text and metadata from data formats such as PDF, images, tables, and charts. Choosing a parsing tool depends on the data format and the complexity of the data (i.e., does the data format contain large tables, pie-charts, mathematical formulas that need to be extracted?).

**Example**

Standard-format PDFs can be handled with rule-based tools such as PDFminer.six, while unstructured PDFs—where text appears in tables or images—often require ML-based tools like PaddleOCR. ML approaches are more robust but demand greater setup effort and expertise compared to simpler methods.

#### 1.1.2 Indexers

Indexers take the extracted text and its metadata, then organize the data into a format such as JSON.

**Example**    

We first identify headings in the PDF—either by looking at their on-page positions (coordinates) or by using an ML model trained to recognize header text. Once we know each section and subsection heading, we split the document into text chunks based on those headings. Finally, we nest those chunks in a hierarchical structure so that every paragraph is stored under the correct section or subsection. This ensures that the text is chunked and stored logically to improve retrieval performance.

![Example Structured JSON](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/example_structured_json.png)

### 1.2 Vector Embedder

Vector embeddings are fixed-length arrays of numbers that capture the semantic meaning of text (words, sentences, paragraphs).

![Example Vector Embeddings](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/example_vector_embeddings.png)

#### 1.2.1 Embedding Model

An embedding model creates vector embeddings. We then store these vector embeddings into a Vector Database for retrieval later on.

We are currently using OpenAI’s embedding model: `text-embedding-large-3`.

#### 1.2.2 Vector Database

A Vector Database is a specialized database that has built-in mathematical functions for storing and manipulating vector embeddings in a high-dimensional space.

We are currently using [Pinecone Vector Database](https://docs.pinecone.io/guides/get-started/overview) because of the easy setup and developer-friendly documentation.

Before the vectors are upserted to Pinecone VDB, a unique “id” key for each text chunk is generated. This “id” key gets stored in the text chunk’s JSON object and the corresponding text embedding, so during the retrieval process the key is returned, and used to map to the text chunk. (This is explained in more detail in the Retrieval section.)

### 1.3 BM25 Tokenizer

Okapi BM25 Retrieval is a keyword-based document retriever that improves on the Term Frequency-Inverse Document Frequency (TF-IDF) ranking algorithm. Term Frequency is the raw count of how many times word *t* appears in document *d*. Inverse Document Frequency is the number of documents *N* divided by the number of documents in which term *t* appears at least once *n<sub>t</sub>*. Therefore, more frequent words such as “the”, “and”, and “is” get less weight. The score of the document is calculated by multiplying TF by IDF.

Given a query Q, containing keywords q₁,...,qₙ, the BM25 score of a document D is:

![Okapi BM25 Scoring Formula](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/okapi_bm25_retrieval_scoring_formula.png)

- score(D, Q): The total BM25 score of document D for query Q.
- D: The document being scored.
- Q: The query, viewed as a sequence of terms (q₁, q₂, …, qₙ).
- n: The number of terms in the query Q.
- i: The index of the current query term (1 through n).
- qᵢ: The i-th term in the query.
- IDF(qᵢ): Inverse document frequency of qᵢ (down-weights common terms).
- f(qᵢ, D): The raw count of how many times qᵢ appears in D.
- k₁: TF-saturation parameter (≥ 0) that controls how quickly term frequency plateaus.
- b: Length-normalization parameter (0 ≤ b ≤ 1) that adjusts for document length.
- |D|: The length of document D (e.g., word count).
- avgdl: The average document length across the corpus (same units as |D|).

#### 1.3.1 Why BM25 instead of TF-IDF?

BM25 adds two parameters.

**TF Saturation (parameter k₁)**

Instead of letting TF grow linearly, BM25 transforms it with,

![BM25 Term Frequency Saturation Parameter](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/bm25_term_frequency_saturation_parameter.png)

so that as a term’s frequency increases, its incremental impact tapers off around k₁ + 1.

**Length Normalization (parameter b)**

Adjusts for document length by computing,

![BM25 Document Length Normalization Parameter](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/bm25_document_length_normalization_parameter.png)

where |*d*| is the length of document *d* and *avgdl* is the average document length. Terms in longer documents get down-weighted, and those in shorter documents get up-weighted, controlled by *b*.

#### 1.3.2 NLTK Tokenizer

The NLTK Tokenizer splits the text document into tokens that are the size of a word or part of a word. These tokenized documents are then stored in the Pickle index.

#### 1.3.3 Pickle Index

Pickle is a Python module that implements binary protocols for serializing and deserializing a Python object structure. Pickle is used instead of JSON because it can store complex Python objects like NumPy arrays and offers faster read/write operations due to its compact binary format. This enables lower-latency BM25 retrieval.

> **Note:** If we have too many documents, we can consider scaling to a production database that supports BM25 retrieval.

## 2 Retrieval

Retrieval is necessary because the LLM does not have direct or up-to-date access to CSHA data, which is external to its pretraining or not reliably reachable by its web search functions. LLMs have limited context windows, charge per input token, and struggle to prioritize relevant information in large inputs. Feeding entire PDFs can exceed the token limit, increase cost, and reduce accuracy.

When a user submits a query to the chat interface, the system augments the prompt with relevant context using one of two retrieval methods: **vector-based retrieval** or **BM25 keyword retrieval**. Both retrievers return the "id"s of the top k documents. These “id”s are used to map to each document’s JSON object, so we can obtain the metadata along with the text chunk. (Pinecone VDB can only return one text field, either an “id” or “text_chunk”, so in order to access the metadata we use an “id” key for mapping.) Once the top "k" document text chunks are retrieved from the JSON, they are combined and added to the user's query as context. Our code organizes the retrieval logic into a modular function, so you can easily switch between vector retrieval and BM25 retrieval as needed.

**Example**

```python
query = "What are effective strategies for retaining adolescent patients?"
retrieval_method = VECTOR_DB

if retrieval_method == VECTOR_DB:
  vector_docs = vector_retriever.retrieve(query)
  print("vector_docs: ", vector_docs)
else:
  bm25_docs = bm25_retriever.retrieve(query)
  print("bm25_docs: ", bm25_docs)
```

```python
"""
Text Document: 
 <text> 'Adolescent-friendly' means that youth are at the table and know what health means to them… [Now as an adult], I don’t hesitate to go to community health centers, and that’s because I know health centers from my SBHC. I may not have the same connections with the staff and the environment. But at least, [my SBHC] increased my knowledge about health services and health, so I can seek the services that I need. - Former SBHC client and youth leader | Modesto, CA Historically, SBHCs have established a model of care that is youth-centered. By applying proactive strategies, SBHCs can commit to adolescent-friendly care despite the changing demands of policy and funding. SBHC providers and staff can continue to guarantee that a student’s visit to a health center is more than just a visit: it can be an informative, empowering, and a memorable moment that can impact a student’s future relationship to healthcare. </text>
<reference>
  <heading> A Commitment to Adolescent-Friendly Care </heading>
  <heading_number> 8 </heading_number>
</reference> 

Text Document: 
 <text> It is important to recognize that not all providers are comfortable working with teens or want to address teen issues. This is not a judgment, just a reality. If SBHCs are going to be successful serving teens, it is essential that they hire staff that want to work with teens. Health care providers should be trained in adolescent health and have experience working with youth.Experienced adolescent health providers can make the visit not only more comfortable but can also increase communication and understanding. </text>
<reference>
  <heading> Hire Health Care Providers Who Have Experience with Youth </heading>
  <heading_number> 4 </heading_number>
  <subheading_number> 1 </subheading_number>
</reference> 
"""
```

> **Note:** Choosing the best retrieval strategy is an ongoing research effort, as there are numerous retrieval techniques to explore—hybrid approaches, which blend the semantic power of vector embeddings with the precision of BM25 keyword scoring, are just one example.

### 2.1 Vector Retriever

#### 2.1.1 Embedding Model

When the user submits their query, the input needs to be converted to a vector so that it can be compared with the vectors in the Pinecone VDB. The same Embedding Model used to create vector embeddings for the processed documents is used for the user queries.

#### 2.1.2 Similarity Comparison Method

To retrieve the most relevant documents from Pinecone VDB we use semantic similarity, measuring how closely related two data points are in meaning or context. There are many semantic similarity metrics including cosine similarity and Euclidean distance. This script uses cosine similarity because it is not affected by the magnitude of the vectors (which can represent the text length or word frequency).

![Cosine and Euclidean Metrics](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/cosine_and_euclidean_metrics.png)

### 2.2 BM25 Retriever

#### 2.2.1 NER Keyword Expander

The NER (Named Entity Recognition) Keyword Expander is a call to an LLM to help expand named entities (names, organizations, events, and locations) in the user query to improve keyword retrieval. The NER Keyword Expander also fixes spelling errors and removes stop-words such as “like”, “and”, and “is”.

**Example**

Input
```
What is the name of the most famous speech by MLK?
```
Output
```
name, famous, speech, MLK, title, designation, well-known, renowned, address, talk, Martin Luther King, Martin Luther King, Jr.
```

#### 2.2.2 Rank BM25

Uses Okapi BM25 to retrieve the top “k” most relevant document “id” keys.

## 3 Prompt Augmentation

A prompt is a text input that tells an AI model (LLM) what response or output to generate. For example, when you ask ChatGPT a question you are prompting it. 

Going forward... Context Engineering over Prompt Engineering.

> “People associate prompts with short task descriptions you'd give an LLM in your day-to-day use.  
> When in every industrial-strength LLM app, context engineering is the delicate art and science of filling the context window with just the right information for the next step.  
> Science because doing this right involves task descriptions and explanations, few shot examples, RAG, related (possibly multimodal) data, tools, state and history, compacting [...]  
> Doing this well is highly non-trivial.  
> And art because of the guiding intuition around LLM psychology of people spirits.”  
>
> — **Andrej Karpathy**

We concatenate the results from the retrieval and add them as part of the context when we instantiate the prompt template. By instructing the LLM to only refer to the context we can generate relevant and accurate responses for the user. 

### 3.1 Prompt Templates

We leverage LangChain’s prompt templates to assemble the messages sent to the language model. These templates are both modular and reusable, so you can dynamically switch to a new prompt template, insert the user’s query, and any contextual information before invoking the LLM for the final response.

**Example**

```python
EXAMPLE_CITATION_TEMPLATE = """
You are a helpful AI assistant that answers using only the provided document snippets. Follow these rules:

1. For each fact you use, cite its source by assigning it a **sequential number** in brackets—first unique source is [1], then [2], etc.  
2. If you use the same snippet again, reuse its original number.  
3. Never invent or skip numbers.

Answer here with your citations inline.

References:
[1] 2.1 Overview of Topic A
[2] 3 Key Findings on Topic B

This is the user query:
```{user_query}```

Here is the context:
```{context}```
"""
```

> **Note: (More Advanced)** Context engineering techniques such as defining the system role, adding delimiters, and providing example I/Os were used to improve the LLM’s response. Better context engineering lets less powerful, lower-cost models match the performance of more expensive ones.

## 4 Generation

The final step of RAG is AI response generation. The completed prompt template is sent to an API (e.g., OpenAI’s API), which passes it as input to the AI model, and the model’s output is returned to the user.

**Example**

```python
"""
------------- AI AGENT RESPONSE -------------

To retain adolescent patients, it is important to create a youth-centered and adolescent-friendly environment where young people feel included and empowered in their healthcare experience. This involves ensuring that staff are committed to adolescent-friendly care and that visits are informative and memorable, which can positively influence future engagement with healthcare services [1]. Additionally, hiring healthcare providers who are trained in adolescent health and have experience working with youth can make visits more comfortable and improve communication and understanding, further supporting retention [2].

        References:
        [1] 8 A Commitment to Adolescent-Friendly Care
        [2] 4.1 Hire Health Care Providers Who Have Experience with Youth
"""
```

### 4.1 Models

Large language models (LLMs) serve as another modular component in our system. Choosing a proprietary LLM lets you skip managing hosting infrastructure and inference costs, since the provider handles all of that. Popular options include [OpenAI](https://platform.openai.com/docs/overview), [Anthropic](https://docs.anthropic.com/en/docs/intro), and [Google](https://ai.google.dev/gemini-api/docs).

We are using OpenAI’s `gpt-4.1`, the most intelligent but expensive OpenAI frontier model.

> **Note:** Choosing the optimal LLM is a research task that requires understanding the cost-intelligence trade-off for specific tasks.

# Installation and Usage

```
pip3 install -r requirements.txt
```

## Dependencies

- `requests` – fetch data from the web
- `pdfminer.six` – parse PDFs
- `nltk` – tokenize text
- `rank_bm25` – BM25 retrieval
- `pinecone` – interface with the Pinecone vector database
- `langchain` – core LangChain tools (e.g., prompt templates)
- `langchain-openai` – LangChain integrations with OpenAI models
- `langchain-pinecone` – LangChain integrations with Pinecone (e.g., `PineconeVectorStore`)

## Environment Variables

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

## Run the Agent

You can download the *Attracting and Retaining Adolescent Patients* PDF here (if you want to test `pdf_parser_indexer.py`): https://drive.google.com/drive/folders/1Kgctv62f9WrOI9ZydvRtXTjeoLObhkcO

**To chat with the AI agent, run the following scripts from the command line:**

Stores Data (BM25 Tokenizer and Vector Embedder)
```
python3 bm25_tokenizer.py
```

```
python3 vector_embedder.py
```

Performs Retrieval, Prompt Augmentation, Generation (Runs a terminal-based chat interface for the AI Agent)
```
python3 user_query_document.py
```

# Known Issues

- `pdf_parser_indexer.py` does not reliably extract text from the PDF or index chunks by heading and subheading because of one-off edge cases, so some manual editing was required to create `structured_text.json`. This JSON file is used for the vector embedder and BM25 tokenizer. A future upgrade is to use a more robust ML-based PDF parser—though we’ll need to weigh the accuracy gains against added development time.
