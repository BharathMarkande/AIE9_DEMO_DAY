import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class OpenAIEmbedder:
    """
    Generates OpenAI embeddings for narrative session summaries.

    Uses OpenAI text-embedding-3-small model for high-quality semantic encoding.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Define your own in .env file.")

        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

    def embed_text(self, text: str) -> list:
        """
        Converts input text into embedding vector.

        Args:
            text (str): Narrative session summary.

        Returns:
            list: Embedding vector.
        """

        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding