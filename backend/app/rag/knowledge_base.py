from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

KNOWLEDGE_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge"

STORE_PATH = Path(__file__).parent.parent.parent / "data" / "vector_store.json"


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
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    for chunk in chunks:
        species = chunk.metadata["species"]
        chunk.page_content = f"Species: {species}\n\n{chunk.page_content}"

    return chunks

def create_vector_store(chunks: list[Document], embeddings):
    store = InMemoryVectorStore.from_documents(chunks, embeddings)
    store.dump(str(STORE_PATH))


def get_vector_store(api_key: str) -> InMemoryVectorStore:
    """Load the saved vector store or build and save it if it doesn't exist yet."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
    )

    if STORE_PATH.exists():
        return InMemoryVectorStore.load(str(STORE_PATH), embeddings)

    chunks = chunk_docs(load_documents())
    store = InMemoryVectorStore.from_documents(chunks, embeddings)
    store.dump(str(STORE_PATH))
    return store

    




    

