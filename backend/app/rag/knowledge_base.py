from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.constants import (
    CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL_NAME, KNOWLEDGE_DIR,
    MARKDOWN_SECTION_HEADERS, VECTOR_STORE_PATH,
)


def load_documents() -> list[Document]:
    documents = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")

        species = path.stem.replace("_", " ").capitalize()
        source = ""
        for line in text.splitlines()[:5]:
            if line.startswith("# "):
                species = line[2:].strip()
            elif line.startswith("Source:"):
                source = line.removeprefix("Source:").strip()
        body_lines = [
        line for line in text.splitlines()
            if not line.startswith(("# ", "Source:", "License:"))
        ]
        text = "\n".join(body_lines).strip()

        documents.append(Document(
            page_content=text,
            metadata={"species": species, "source": source, "file": path.name},
        ))
    return documents

def chunk_docs(docs: list[Document]) -> list[Document]:
    """Split each article by section, then split long sections by size.
    Every chunk records its section, e.g. "Description > Similar species"."""
    header_splitter = MarkdownHeaderTextSplitter(MARKDOWN_SECTION_HEADERS)
    size_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = []

    for doc in docs:
        for section in header_splitter.split_text(doc.page_content):
            headers = [section.metadata[key] for _, key in MARKDOWN_SECTION_HEADERS if key in section.metadata]
            section_name = " > ".join(headers) or "Introduction"
            metadata = {**doc.metadata, "section": section_name}

            for piece in size_splitter.split_text(section.page_content):
                chunks.append(Document(
                    page_content=f"Species: {doc.metadata['species']}\nSection: {section_name}\n\n{piece}",
                    metadata=metadata,
                ))

    return chunks

def create_vector_store(chunks: list[Document], embeddings) -> InMemoryVectorStore:
    store = InMemoryVectorStore.from_documents(chunks, embeddings)
    store.dump(str(VECTOR_STORE_PATH))
    return store


def get_vector_store(api_key: str) -> InMemoryVectorStore:
    """Load the saved vector store or build and save it if it doesn't exist yet."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        google_api_key=api_key,
    )

    if VECTOR_STORE_PATH.exists():
        return InMemoryVectorStore.load(str(VECTOR_STORE_PATH), embeddings)

    return create_vector_store(chunk_docs(load_documents()), embeddings)
