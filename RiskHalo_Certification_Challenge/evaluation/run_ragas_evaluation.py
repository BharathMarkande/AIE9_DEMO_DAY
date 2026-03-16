import argparse

from evaluation.ragas_eval import RiskHaloRagasEvaluator


def print_results(title, results):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    try:
        for metric, value in results.items():
            print(f"{metric}: {round(value, 4)}")
    except Exception:
        print(results)


def main():
    parser = argparse.ArgumentParser(
        description="Run RiskHalo RAGAS evaluation (baseline or multi-query retriever)."
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Use single-query (baseline) retriever instead of multi-query.",
    )
    args = parser.parse_args()
    use_multi_query = not args.baseline

    retriever_label = "baseline (single-query)" if args.baseline else "multi-query"
    print("\nStarting Simplified RiskHalo RAGAS Evaluation...")
    print(f"Retriever: {retriever_label}\n")

    evaluator = RiskHaloRagasEvaluator(use_multi_query=use_multi_query)

    results = evaluator.evaluate()

    print_results(
        f"RAGAS Evaluation ({retriever_label}) - Overall metrics (mean)", results
    )

    # per-question metrics
    df = results.to_pandas()
    cols = [
        "user_input",
        "context_recall",
        "context_entity_recall",
        "context_precision",
        "faithfulness",
        "answer_relevancy",
    ]
    print(f"\nRAGAS Evaluation ({retriever_label}) - per-question metrics")
    print(df[cols])

    print("\nEvaluation Completed.\n")


if __name__ == "__main__":
    main()