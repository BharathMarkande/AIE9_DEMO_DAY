import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rag.vector_store import RiskHaloVectorStore

def retrieve_and_print_doc_count() -> None:
    """
    Connects to the existing ChromaDB persistent store,
    retrieves all stored documents from the RiskHalo collection,
    and prints the number of documents retrieved.
    """

    vector_store = RiskHaloVectorStore()

    # Fetch all documents currently stored in the collection
    results = vector_store.collection.get()
    documents = results.get("documents", []) if results else []

    print(f"Number of documents retrieved from ChromaDB: {len(documents)}")


if __name__ == "__main__":
    retrieve_and_print_doc_count()

