# csha-ai-agent

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

Working on a technical explanation due this Friday!!!

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
