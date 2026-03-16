"""
Multi-query retriever for RiskHalo.

This module extends the basic `RiskHaloRetriever` by:
- Generating multiple reformulated queries from the user's question using the LLM
- Running vector search for each reformulation
- Merging and de-duplicating the retrieved documents

Goal:
- Broaden the retrieval set to improve grounding and RAGAS context metrics
  (e.g., context recall, faithfulness), especially when the original query
  is underspecified or phrased in a narrow way.
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any
from openai import OpenAI

from rag.prompts import MULTI_QUERY_SYSTEM_PROMPT, MULTI_QUERY_USER_PROMPT_TEMPLATE
from rag.retriever import RiskHaloRetriever


class MultiQueryRiskHaloRetriever(RiskHaloRetriever):
    """
    Multi-query variant of `RiskHaloRetriever`.

    High-level flow:
    1. Use the LLM to generate multiple alternative queries for the user question
       (rephrasings, decompositions, and angle variations).
    2. Perform vector retrieval for each of these queries against ChromaDB.
    3. Merge and de-duplicate the retrieved documents.
    4. Build the grounding prompt and generate the final answer.
    """

    def __init__(
        self,
        collection_name: str = "riskhalo_sessions",
        top_k: int = 6,
        model: str = "gpt-4o-mini",
        persist_directory: str = "./chroma_db",
        num_query_variants: int = 3,
    ) -> None:
        """
        Parameters
        ----------
        collection_name : str
            ChromaDB collection name.
        top_k : int
            Final number of documents to keep after merging results.
        model : str
            Chat model used both for answer generation and query expansion.
        persist_directory : str
            ChromaDB persistence directory.
        num_query_variants : int
            Number of *additional* query reformulations to generate
            (not counting the original user question).
        """
        super().__init__(
            collection_name=collection_name,
            top_k=top_k,
            model=model,
            persist_directory=persist_directory,
        )

        self.llm: OpenAI = OpenAI()
        self.num_query_variants = max(1, num_query_variants)

    # --------------------------------------------------
    # Query Expansion
    # --------------------------------------------------
    def _generate_query_variants(self, question: str) -> List[str]:
        """
        Uses the chat model to generate multiple alternative queries.

        Returns a list of reformulated queries (without the original question).
        """
        system_prompt = MULTI_QUERY_SYSTEM_PROMPT
        user_prompt = MULTI_QUERY_USER_PROMPT_TEMPLATE.format(
            num_query_variants=self.num_query_variants,
            question=question,
        ).strip()

        response = self.llm.chat.completions.create(
            model=self.model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or ""
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

        # Deduplicate while preserving order and cap to num_query_variants.
        seen = set()
        variants: List[str] = []
        for ln in lines:
            if ln not in seen:
                seen.add(ln)
                variants.append(ln)
            if len(variants) >= self.num_query_variants:
                break

        return variants

    # --------------------------------------------------
    # Multi-query Retrieval
    # --------------------------------------------------
    def multi_retrieve(
        self, question: str, metadata_filter: Dict[str, Any] | None = None
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Runs retrieval for the original question and its query variants, then
        merges and de-duplicates the results.

        Returns
        -------
        documents : list[str]
            Aggregated top-k session summaries.
        metadatas : list[dict]
            Corresponding metadata entries.
        """
        # 1) Expand to multiple queries
        variants = self._generate_query_variants(question)
        all_queries = [question] + variants

        aggregated_docs: List[str] = []
        aggregated_metas: List[Dict[str, Any]] = []

        # Simple de-duplication based on (document, metadata) fingerprint.
        seen_keys = set()

        for q in all_queries:
            docs, metas = super().retrieve(q, metadata_filter=metadata_filter)
            for doc, meta in zip(docs, metas):
                key = (doc, repr(sorted(meta.items())) if isinstance(meta, dict) else repr(meta))
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                aggregated_docs.append(doc)
                aggregated_metas.append(meta)

        # Truncate to configured top_k
        if len(aggregated_docs) > self.top_k:
            aggregated_docs = aggregated_docs[:self.top_k]
            aggregated_metas = aggregated_metas[: self.top_k]

        return aggregated_docs, aggregated_metas

    # --------------------------------------------------
    # End-to-end Generation (Multi-query)
    # --------------------------------------------------
    def generate(
        self, question: str, metadata_filter: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        End-to-end multi-query RAG pipeline:
        - Expand question into multiple queries
        - Retrieve merged context
        - Build prompt
        - Generate structured answer

        This mirrors `RiskHaloRetriever.generate` but swaps in `multi_retrieve`.
        """
        retrieved_contexts, retrieved_metadatas = self.multi_retrieve(
            question, metadata_filter=metadata_filter
        )

        if not retrieved_contexts:
            return {
                "question": question,
                "retrieved_contexts": [],
                "retrieved_metadatas": [],
                "answer": "No relevant session data found.",
            }

        system_prompt, user_prompt = self.build_prompt(
            question,
            retrieved_contexts,
        )

        response = self.llm.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        answer = response.choices[0].message.content

        return {
            "question": question,
            "retrieved_contexts": retrieved_contexts,
            "retrieved_metadatas": retrieved_metadatas,
            "answer": answer,
        }

