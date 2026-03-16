from datetime import datetime
from app.expectancy_engine import format_expectancy_summary
import hashlib


class SessionSummaryBuilder:
    """
    Creates a structured behavioral snapshot for a given analysis session.

    Combines behavioral diagnosis and financial impact into:
    - Structured JSON (machine-readable)
    - Narrative summary (embedding-ready text)
    - Metadata (retrieval filtering)

    It represents a single time-stamped behavioral checkpoint
    in the trader's performance evolution.
    """

    def __init__(self, feature_df, behavioral_output: dict, expectancy_output: dict, rule_results: dict):
        self.df = feature_df
        self.behavior = behavioral_output
        self.expectancy = expectancy_output
        self.rules = rule_results
        self.total_trades = len(feature_df)

    # --------------------------------------------------
    # Generate Unique Session ID
    # --------------------------------------------------
    def generate_session_id(self):
        """
        Generates deterministic session ID based on trade data content.

        Identical uploads → identical session_id.
        Prevents duplicate vector entries.
        """

        # Ensure consistent ordering
        df_sorted = self.df.sort_values(by=list(self.df.columns))

        content_string = df_sorted.to_csv(index=False)

        content_hash = hashlib.md5(content_string.encode()).hexdigest()[:12]

        return f"session_{content_hash}"

    # --------------------------------------------------
    # Build Structured Snapshot (JSON)
    # --------------------------------------------------
    def build_structured_summary(self):
        """
        Creates a structured JSON snapshot of the session.

        Combines behavioral classification, distortion metrics,
        expectancy shifts, and financial impact into a single
        machine-readable record.

        This snapshot represents the trader’s behavioral state
        at a specific point in time.
        """

        self.session_id = self.generate_session_id()
        self.timestamp = datetime.now().isoformat()

        self.structured_summary = {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "total_trades": self.total_trades,

            "behavioral_state": self.behavior["behavioral_state"],
            "severity_score": self.behavior["severity_score"],

            "avg_R_normal": self.behavior["avg_R_normal"],
            "avg_R_post": self.behavior["avg_R_post"],

            "R_drop_percent": self.behavior["R_drop_percent"],
            "win_shrink_percent": self.behavior["win_shrink_percent"],
            "loss_expansion_percent": self.behavior["loss_expansion_percent"],

            "expectancy_normal_R": self.expectancy["expectancy_normal_R"],
            "expectancy_post_R": self.expectancy["expectancy_post_R"],
            "expectancy_delta_R": self.expectancy["expectancy_delta_R"],

            "economic_impact_rupees": self.expectancy["economic_impact_rupees"]
        }

        return self.structured_summary

    # ==========================================================
    # Narrative — Rule Compliance Section
    # ==========================================================
    def build_rule_narrative(self):

        violations = self.rules["violations"]
        scores = self.rules["discipline_scores"]

        discipline_score = scores["overall_discipline_score"]
        
        risk_breach = violations["risk_breach_count"]
        rr_violation = violations["rr_violation_count"]
        overtrading_days = violations["overtrading_days"]
        daily_loss_breaches = violations["daily_loss_breaches"]

        narrative_parts = []

        # --------------------------------------------------
        # Overall framing
        # --------------------------------------------------
        if discipline_score >= 85:
            narrative_parts.append(
                f"Execution discipline was strong this week (Score: {discipline_score}/100)."
            )
        elif discipline_score >= 65:
            narrative_parts.append(
                f"Execution discipline was moderate this week (Score: {discipline_score}/100), with identifiable areas for tightening."
            )
        else:
            narrative_parts.append(
                f"Execution discipline was inconsistent this week (Score: {discipline_score}/100), with structural rule breaches affecting stability."
            )

        # --------------------------------------------------
        # Risk management
        # --------------------------------------------------
        if risk_breach == 0:
            narrative_parts.append(
                "Risk per trade was respected across positions."
            )
        else:
            narrative_parts.append(
                f"{risk_breach} trade(s) exceeded declared risk, indicating lapses in loss containment."
            )

        # --------------------------------------------------
        # Daily loss containment
        # --------------------------------------------------
        if daily_loss_breaches == 0:
            narrative_parts.append(
                "Daily loss limits were maintained."
            )
        else:
            narrative_parts.append(
                f"{daily_loss_breaches} day(s) breached maximum daily loss, increasing capital volatility."
            )

        # --------------------------------------------------
        # Overtrading control
        # --------------------------------------------------
        if overtrading_days == 0:
            narrative_parts.append(
                "Trade frequency remained within planned limits."
            )
        else:
            narrative_parts.append(
                f"Overtrading occurred on {overtrading_days} day(s), suggesting emotional or reactive participation."
            )

        # --------------------------------------------------
        # R:R discipline
        # --------------------------------------------------
        if rr_violation == 0:
            narrative_parts.append(
                "Profit targets were aligned with minimum reward expectations."
            )
        else:
            narrative_parts.append(
                f"{rr_violation} winning trade(s) closed below minimum R:R threshold, reflecting premature profit capture."
            )

        return " ".join(narrative_parts)

    # --------------------------------------------------
    # Convert Snapshot to Narrative Text
    # --------------------------------------------------
    def build_narrative_summary(self):
        """
        Converts structured metrics into a performance-coach style narrative.

        The narrative explains:
        - Behavioral state classification
        - Expectancy shift magnitude
        - Financial impact of distortion

        This text is designed for semantic embedding and
        downstream retrieval in the RAG system.
        """
        state = self.behavior["behavioral_state"]
        severity = round(self.behavior["severity_score"], 2)

        exp_normal = round(self.expectancy["expectancy_normal_R"], 2)
        exp_post = round(self.expectancy["expectancy_post_R"], 2)
        exp_delta = round(self.expectancy["expectancy_delta_R"], 2)
        rupee_impact = round(self.expectancy["economic_impact_rupees"])

        # State-based interpretation
        if state == "ADAPTIVE_RECOVERY":
            interpretation = (
                "You tend to improve execution after losses rather than deteriorate. "
                "This reflects emotional resilience and controlled risk behavior."
            )

        elif state == "LOSS_ESCALATION":
            interpretation = (
                "Losses expand following losing trades, indicating emotional risk escalation. "
                "Reducing downside variance after drawdowns should be a priority."
            )

        elif state == "CONFIDENCE_CONTRACTION":
            interpretation = (
                "Win size decreases after losses, suggesting hesitation or reduced conviction. "
                "Maintaining structured execution after setbacks is critical."
            )

        else:  # STABLE
            interpretation = (
                "Your performance remains consistent regardless of recent losses. "
                "This indicates disciplined execution and stable risk management."
            )

        formatted_expectancy = format_expectancy_summary(
            exp_normal,
            exp_post,
            exp_delta,
            rupee_impact,
            state,
            risk_per_trade=self.expectancy.get("risk_per_trade")
        )

        narrative = (
            f"In this session of {self.total_trades} trades, you were classified as {state} "
            f"(severity {severity}).\n\n"
            f"{interpretation}\n\n"
            f"{formatted_expectancy}"
        )

        self.narrative_summary = narrative
        return narrative

    # --------------------------------------------------
    # Metadata for Vector DB
    # --------------------------------------------------
    def build_metadata(self):
        """
        Generates metadata for vector database storage.

        Includes key retrieval fields such as:
        - session_id
        - timestamp
        - behavioral_state
        - severity_score
        - total_trades

        Metadata enables hybrid retrieval and filtering
        across historical behavioral snapshots.
        """

        metadata = {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "behavioral_state": self.behavior["behavioral_state"],
            "severity_score": self.behavior["severity_score"],
            "total_trades": self.total_trades
        }

        return metadata

    # --------------------------------------------------
    # Run Full Session Summary Builder
    # --------------------------------------------------
    def run(self):
        """
        Executes the full session snapshot construction pipeline:

        1. Generate unique session identifier
        2. Build structured summary (JSON)
        3. Generate narrative behavioral summary
        4. Prepare retrieval metadata

        Returns a complete snapshot object ready for
        embedding and vector database storage.
        """

        structured = self.build_structured_summary()
        narrative = self.build_narrative_summary()
        metadata = self.build_metadata()
        rule_narrative = self.build_rule_narrative()

        return {
            "structured_summary": structured,
            "narrative_summary": narrative,
            "rule_narrative": rule_narrative,
            "metadata": metadata
        }