from langchain_core.documents import Document


def to_result(doc: Document) -> dict:
    return {
        "species": doc.metadata["species"],
        "section": doc.metadata.get("section", ""),
        "source": doc.metadata["source"],
        "text": doc.page_content,
    }
