from ragas import evaluate, RunConfig
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    LLMContextRecall,
    Faithfulness,
    ResponseRelevancy,
    ContextEntityRecall,
    ContextPrecision,
)
from datasets import Dataset
from evaluation.generate_testset import RiskHaloTestsetGenerator
from rag.retriever import RiskHaloRetriever
from rag.multi_query_retriever import MultiQueryRiskHaloRetriever
from evaluation.personas import TRADER_PERSONAS


class RiskHaloRagasEvaluator:
    """
    Simplified RAGAS Evaluation for MVP.

    Uses:
    - Single concatenated raw document
    - 10 persona-driven questions
    - Full metric set
    """

    def __init__(self, use_multi_query: bool = True):
        self.llm = LangchainLLMWrapper(
            ChatOpenAI(model="gpt-4o-mini", temperature=0)
        )
        self.embedding_model = OpenAIEmbeddings()
        self.testset_generator = RiskHaloTestsetGenerator()

        # Use multi-query retriever by default to improve context recall and
        # other RAGAS metrics, while keeping an easy option to fall back to the
        # baseline single-query retriever for comparison.
        if use_multi_query:
            self.retriever = MultiQueryRiskHaloRetriever()
        else:
            self.retriever = RiskHaloRetriever()

    # --------------------------------------------------
    # Prepare RAGAS Dataset
    # --------------------------------------------------
    def prepare_ragas_dataset(self):
        """
        Builds RAGAS dataset using persona-aligned ground truth.

        For each persona:
        - Filter sessions by behavioral_state
        - Concatenate matching sessions as ground truth
        - Generate 2 evaluation questions
        - Run full RAG pipeline
        """

        ragas_rows = []

        # Fetch all sessions once
        data = self.retriever.collection.get(include=["documents", "metadatas"])
        
        print(f"prepare_ragas_dataset::data length: {len(data)}")
        all_docs = data.get("documents", [])
        all_meta = data.get("metadatas", [])

        print(f"prepare_ragas_dataset::num documents: {len(all_docs)}")

        # Flatten if nested
        if all_docs and isinstance(all_docs[0], list):
            all_docs = all_docs[0]

        sessions = list(zip(all_docs, all_meta))

        for persona_name, persona in TRADER_PERSONAS.items():

            target_state = persona["behavioral_state"]
            questions = persona["question_templates"][:2]

            # -----------------------------------------
            # Filter sessions matching persona state
            # -----------------------------------------
            matching_sessions = [
                doc for doc, meta in sessions
                if meta.get("behavioral_state") == target_state
            ]

            # If no sessions match this persona's behavioral_state,
            # fall back to using all available sessions so that
            # RAGAS still has data to evaluate on.
            if not matching_sessions:
                matching_sessions = [doc for doc, _ in sessions]

            # Persona-specific ground truth
            ground_truth_context = "\n\n".join(matching_sessions)

            # -----------------------------------------
            # For each question → run RAG
            # -----------------------------------------
            for question in questions:

                #rag_result = self.retriever.generate(question)
                rag_result = self.retriever.generate(
                    question,
                    metadata_filter={"behavioral_state": target_state}
                )

                answer = rag_result["answer"]
                retrieved_contexts = rag_result["retrieved_contexts"]
                retrieved_metadatas = rag_result["retrieved_metadatas"]

                print("Target State:", target_state)
                print("Retrieved States:", [
                    meta.get("behavioral_state")
                    for meta in retrieved_metadatas
                ])

                ragas_rows.append(
                    {
                        "question": question,
                        "contexts": retrieved_contexts,
                        "ground_truth": ground_truth_context,
                        "response": answer,
                    }
                )

        return Dataset.from_list(ragas_rows)
    # --------------------------------------------------
    # Run Evaluation
    # --------------------------------------------------
    def evaluate(self):

        ragas_data = self.prepare_ragas_dataset()

        custom_run_config = RunConfig(timeout=360)

        print(f"Start RAGAS evaluation")
        print(f"evaluate::ragas_data length: {len(ragas_data)}")
        results = evaluate(
            ragas_data,
            metrics=[
                LLMContextRecall(),
                ContextPrecision(),
                ContextEntityRecall(),
                Faithfulness(),
                ResponseRelevancy()
            ],
            llm=self.llm,
            run_config=custom_run_config,
        )

        return results