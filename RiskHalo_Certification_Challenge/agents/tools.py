# agents/tools.py

import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch


load_dotenv()


class TavilySearchTool:
    """
    External knowledge retrieval tool using Tavily API via langchain_tavily.

    This tool is used when a user question requires:
    - Behavioral finance research
    - Psychology explanations
    - Risk management best practices
    - External validation beyond stored session data

    It returns summarized web results to be incorporated
    into the agent's reasoning process.
    """

    def __init__(self, max_results: int = 3, topic: str = "general", search_depth: str = "basic"):
        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables. Define your own in .env file.")

        self._tool = TavilySearch(
            max_results=max_results,
            topic=topic,
            search_depth=search_depth,
        )

    def search(self, query: str, max_results: int | None = None) -> str:
        """
        Performs external search using Tavily via langchain_tavily.

        Args:
            query (str): User question
            max_results (int | None): Ignored; max_results is set at instantiation.
                Kept for backward compatibility.

        Returns:
            str: Concatenated summarized results
        """
        response = self._tool.invoke({"query": query})

        summaries = []
        results = response.get("results", [])

        for result in results:
            title = result.get("title", "")
            content = result.get("content", "")
            summaries.append(f"{title}: {content}")

        answer = response.get("answer")
        if answer:
            summaries.insert(0, f"Answer: {answer}")

        return "\n\n".join(summaries) if summaries else ""
