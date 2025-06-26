import json
import os
from uuid import uuid4
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from tqdm.auto import tqdm

def initialize_openai_embeddings(model_name: str, api_key: str) -> OpenAIEmbeddings:
    """Initialize OpenAI embedding model."""
    return OpenAIEmbeddings(model=model_name, openai_api_key=api_key)

def initialize_pinecone(api_key: str, index_name: str):
    """Initialize Pinecone index, creating it if it does not exist."""
    pc = Pinecone(api_key=api_key)

    try:
        pc.describe_index(index_name)
    except Exception:
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=3072,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-west-2"
                )
            )

    return pc.Index(index_name)

def generate_unique_embedding_id() -> str:
    """Generate a unique UUID string for embedding IDs."""
    return str(uuid4())

def create_and_upsert_embedding(
    text: str,
    embedding_id: str,
    metadata: dict,
    embed: OpenAIEmbeddings,
    index
) -> str:
    """
    Create an embedding from the given text and upsert it to the vector index.
    
    Args:
        text: The input text to embed.
        embedding_id: Unique identifier for the embedding.
        metadata: Dictionary with metadata to attach to the embedding.
        embed: Embedding model instance.
        index: Pinecone index object.
    
    Returns:
        The embedding ID.
    """
    embed_vector = embed.embed_documents([text])[0]
    metadata["id"] = embedding_id
    metadata["text_snippet"] = " ".join(text.split()[:50])
    
    index.upsert(
        vectors=[(embedding_id, embed_vector, metadata)],
    )

    print(
        f"Upserted embedding for {metadata.get('heading_title')} / "
        f"{metadata.get('subheading_title', '')} → ID {embedding_id}"
    )
    
    return embedding_id

def process_json_and_create_embeddings(
    json_path: str,
    embed: OpenAIEmbeddings,
    index
) -> None:
    """
    Process a structured JSON file and embed each heading and subheading.
    
    Args:
        json_path: Path to the JSON file.
        embed: OpenAI embeddings instance.
        index: Pinecone index object.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for heading in tqdm(data["headings"], desc="Headings"):
        title = heading["heading_title"]

        # Skip the final "Sources" section
        if title.strip().lower() == "sources":
            continue

        # Embed the heading's own text, if available
        heading_text = heading.get("text", "").strip()
        if heading_text:
            metadata = {"heading_title": title}
            embedding_id = generate_unique_embedding_id()
            heading["id"] = create_and_upsert_embedding(
                heading_text, embedding_id, metadata, embed, index
            )

        # Embed each subheading
        for sub in heading.get("subheadings", []):
            sub_text = sub.get("text", "").strip()
            if not sub_text:
                continue

            metadata = {
                "heading_title": title,
                "subheading_title": sub.get("subheading_title", "").strip()
            }

            embedding_id = generate_unique_embedding_id()
            sub["id"] = create_and_upsert_embedding(
                sub_text, embedding_id, metadata, embed, index
            )

    # Save updated data with embedding IDs
    with open("output/structured_text_with_ids.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main() -> None:
    """Main script execution."""
    # Load environment variables
    OPENAI_API_KEY = os.environ["OPENAI_API_EMBEDDINGS_KEY"]
    PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]

    # Initialize embeddings and Pinecone index
    index_name = "attracting-and-retaining-adolescent-patients"
    embed = initialize_openai_embeddings("text-embedding-3-large", OPENAI_API_KEY)
    index = initialize_pinecone(PINECONE_API_KEY, index_name)

    # Process the input JSON file
    input_json_file = "output/structured_text.json"
    process_json_and_create_embeddings(input_json_file, embed, index)

if __name__ == "__main__":
    main()