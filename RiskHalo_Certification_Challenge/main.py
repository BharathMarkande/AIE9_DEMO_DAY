import os
import glob
import traceback

from app.parser import TradeParser
from app.feature_engine import FeatureEngine
from app.behavioral_engine import BehavioralEngine
from app.expectancy_engine import ExpectancyEngine
from app.session_summary_builder import SessionSummaryBuilder
from app.rule_engine import RuleComplianceEngine
from app.config_loader import load_rules_config


from rag.embedder import OpenAIEmbedder
from rag.vector_store import RiskHaloVectorStore
from agents.coach_agent import ask_coach

DECLARED_RISK = 2000
DATA_FOLDER = "data/Weekly_Trade_Data_Uploads"


def process_single_file(file_path, embedder, vector_store, declared_risk=None):
    """
    Runs full RiskHalo pipeline for a single weekly file
    and stores its summary in ChromaDB.
    """
    risk = declared_risk if declared_risk is not None else DECLARED_RISK

    print(f"\n Processing file: {file_path}")

    # ----------------------------
    # Analytics Layer
    # ----------------------------
    parser = TradeParser(file_path)
    df = parser.parse()

    feature_df = FeatureEngine(df, risk).run()
    diagnosis = BehavioralEngine(feature_df).run()

    post_loss_trade_count = int(feature_df["post_loss_flag"].sum())

    impact = ExpectancyEngine(
        diagnosis,
        risk,
        len(feature_df),
        post_loss_trade_count
    ).run()

    # ==========================================================
    # Rule Compliance Layer
    # ==========================================================
    rules_config = load_rules_config()
    rule_engine = RuleComplianceEngine(feature_df, rules_config)
    rule_results = rule_engine.run()


    # ----------------------------
    # Build Summary Snapshot
    # ----------------------------
    builder = SessionSummaryBuilder(feature_df, diagnosis, impact, rule_results)
    snapshot = builder.run()

    session_id = snapshot["structured_summary"]["session_id"]
    narrative = snapshot["narrative_summary"]
    rule_narrative = snapshot["rule_narrative"]

    full_narrative = (narrative if isinstance(narrative, str) else "\n\n".join(narrative)) + "\n\n" + rule_narrative

    print("=" * 60)
    print(f"session_id: {session_id}")
    print(f"Full narrative: {full_narrative}")
    print("=" * 60)

    # ----------------------------
    # Embed Narrative
    # ----------------------------
    embedding = embedder.embed_text(full_narrative)

    # ----------------------------
    # Store in ChromaDB with Metadata
    # ----------------------------

    discipline_score = rule_results["discipline_scores"]["overall_discipline_score"]
    metadata = {
        "session_id": session_id,
        "behavioral_state": diagnosis["behavioral_state"],
        "severity_score": diagnosis["severity_score"],
        "discipline_score": discipline_score,
        "risk_breach_count": rule_results["violations"]["risk_breach_count"],
        "rr_violation_count": rule_results["violations"]["rr_violation_count"], # Risk:Reward violation count
        "overtrading_days": rule_results["violations"]["overtrading_days"],
        "daily_loss_breaches": rule_results["violations"]["daily_loss_breaches"],
    }

    vector_store.add_session(
        session_id=session_id,
        embedding=embedding,
        document=full_narrative,
        metadata=metadata
    )

    print(f"Stored session in vector DB: {session_id}")

    # ----------------------------
    # Return analysis payload for API response
    # ----------------------------
    structured = snapshot["structured_summary"]
    expectancy = {
        "expectancy_normal_R": structured.get("expectancy_normal_R"),
        "expectancy_post_R": structured.get("expectancy_post_R"),
        "expectancy_delta_R": structured.get("expectancy_delta_R"),
        "economic_impact_rupees": structured.get("economic_impact_rupees"),
    }
    behavioral_narrative = narrative if isinstance(narrative, str) else "\n\n".join(narrative)
    return {
        "session_id": session_id,
        "behavioral_state": diagnosis["behavioral_state"],
        "severity_score": round(float(diagnosis["severity_score"]), 2),
        "expectancy_summary": expectancy,
        "discipline_score": round(float(discipline_score), 2),
        "narrative_summary": behavioral_narrative,
        "rule_narrative": rule_narrative,
    }


def run_pipeline():

    # --------------------------------
    # Initialize shared components
    # --------------------------------
    embedder = OpenAIEmbedder()
    vector_store = RiskHaloVectorStore()

    # --------------------------------
    # Find all weekly Excel files (exclude Excel lock files ~$*.xlsx)
    # --------------------------------
    all_xlsx = glob.glob(os.path.join(DATA_FOLDER, "*.xlsx"))
    file_paths = [
        f for f in all_xlsx
        if not os.path.basename(f).startswith("~$")
    ]

    if not file_paths:
        print("No weekly trade files found.")
        return

    print(f"\n Found {len(file_paths)} weekly trade files.")

    # --------------------------------
    # Process each file
    # --------------------------------
    for file_path in file_paths:
        try:
            process_single_file(file_path, embedder, vector_store)
        except Exception as e:
            print(f" Error processing {file_path}: {e}")
            traceback.print_exc()

    print("\n  All weekly files processed successfully.")


if __name__ == "__main__":
    run_pipeline()