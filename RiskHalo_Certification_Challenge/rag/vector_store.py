import chromadb
from chromadb.config import Settings


class RiskHaloVectorStore:
    """
    Manages persistent storage of behavioral session snapshots
    in ChromaDB.
    """

    def __init__(self, persist_directory: str = "./chroma_db"):

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="riskhalo_sessions"
        )

    def add_session(self, session_id: str, embedding: list, document: str, metadata: dict):
        """
        Stores a new session snapshot in the vector database.

        Args:
            session_id (str): Unique session identifier.
            embedding (list): Embedding vector.
            document (str): Narrative summary.
        """

        self.collection.upsert(
            ids=[session_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata] if metadata else None
        )