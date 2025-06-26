# csha-ai-agent

## About

A simple AI agent with a CLI chat interface that answers questions about the
[*Attracting and Retaining Adolescent Patients* PDF](https://drive.google.com/drive/folders/1Kgctv62f9WrOI9ZydvRtXTjeoLObhkcO) provided by CSHA
(non-profit). Built with a Retrieval-Augmented Generation (RAG) framework.

## RAG Architecture

![RAG architecture](https://github.com/ManiacUrgency42/csha-ai-agent/blob/main/assets/images/rag_pipeline_tech_stack_architecture_diagram.png)

## Installation and Usage

```
pip3 install -r requirements.txt
```

Dependencies:

- `requests` – fetch data from the web
- `pdfminer.six` – parse PDFs
- `nltk` – tokenize text
- `rank_bm25` – BM25 retrieval
- `pinecone` – interface with the Pinecone vector database
- `langchain` – core LangChain tools (e.g., prompt templates)
- `langchain-openai` – LangChain integrations with OpenAI models
- `langchain-pinecone` – LangChain integrations with Pinecone (e.g., `PineconeVectorStore`)

You can dowload the *Attracting and Retaining Adolescent Patients* PDF here: https://drive.google.com/drive/folders/1Kgctv62f9WrOI9ZydvRtXTjeoLObhkcO

`pdf_parser_indexer.py` does not smoothly extract the text from the PDF document and index the text chunks properly by heading and subheading, so a bit of manual work was needed to prepare the JSON formatted data for embedding or tokenizing.
The `structured_text.json` is the manually edited JSON output file. You can still run the `pdf_parser_indexer.py` to see the result, but make sure to use `structured_text.json` for the vector embedder and bm25 tokenizer.  
