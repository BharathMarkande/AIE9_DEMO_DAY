"""Tests for app.session_summary_builder SessionSummaryBuilder."""

import pytest
import json
from pathlib import Path

from app.session_summary_builder import SessionSummaryBuilder

TEST_TRADE_DATA_PATH = Path(__file__).resolve().parent / "data" / "test_trade_data.xlsx"


class TestSessionSummaryBuilder:
    """Tests for SessionSummaryBuilder class (uses tests/data/test_trade_data.xlsx)."""

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_run_returns_expected_keys(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """SessionSummaryBuilder.run() returns dict with structured_summary, narrative_summary, metadata."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        assert isinstance(result, dict)
        assert "structured_summary" in result
        assert "narrative_summary" in result
        assert "metadata" in result

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_structured_summary_has_expected_keys(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """structured_summary contains all expected fields."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        structured = result["structured_summary"]
        expected_keys = [
            "session_id",
            "timestamp",
            "total_trades",
            "behavioral_state",
            "severity_score",
            "avg_R_normal",
            "avg_R_post",
            "R_drop_percent",
            "win_shrink_percent",
            "loss_expansion_percent",
            "expectancy_normal_R",
            "expectancy_post_R",
            "expectancy_delta_R",
            "economic_impact_rupees",
            "simulated_rupee_improvement",
        ]
        for key in expected_keys:
            assert key in structured, f"Missing key: {key}"

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_structured_summary_matches_behavioral_and_expectancy(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """structured_summary values match behavioral and expectancy inputs."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        structured = result["structured_summary"]
        assert structured["behavioral_state"] == behavioral_test_trade_data["behavioral_state"]
        assert structured["severity_score"] == behavioral_test_trade_data["severity_score"]
        assert structured["expectancy_normal_R"] == expectancy_test_trade_data["expectancy_normal_R"]
        assert structured["expectancy_post_R"] == expectancy_test_trade_data["expectancy_post_R"]
        assert structured["economic_impact_rupees"] == expectancy_test_trade_data["economic_impact_rupees"]
        assert structured["total_trades"] == total_trades

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_narrative_summary_contains_elements(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """narrative_summary is a string containing state, severity, total_trades, economic impact."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        narrative = result["narrative_summary"]
        assert isinstance(narrative, str)
        assert str(total_trades) in narrative
        assert behavioral_test_trade_data["behavioral_state"] in narrative
        assert str(behavioral_test_trade_data["severity_score"]) in narrative
        assert "₹" in narrative or "rupees" in narrative.lower() or str(expectancy_test_trade_data["economic_impact_rupees"]) in narrative

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_metadata_has_expected_keys(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """metadata contains session_id, timestamp, behavioral_state, severity_score, total_trades."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        metadata = result["metadata"]
        assert "session_id" in metadata
        assert "timestamp" in metadata
        assert "behavioral_state" in metadata
        assert "severity_score" in metadata
        assert "total_trades" in metadata

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_session_id_format(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """session_id starts with 'session_' and contains timestamp pattern."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        session_id = result["structured_summary"]["session_id"]
        assert session_id.startswith("session_")
        assert "_" in session_id
        assert len(session_id) > 20

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_print_structured_and_narrative_summary(
        self, behavioral_test_trade_data: dict | None, expectancy_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """Print structured_summary and narrative_summary (run with pytest -s to see output)."""
        assert behavioral_test_trade_data is not None
        assert expectancy_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        builder = SessionSummaryBuilder(
            behavioral_test_trade_data,
            expectancy_test_trade_data,
            total_trades,
        )
        result = builder.run()
        structured_summary = result["structured_summary"]
        narrative_summary = result["narrative_summary"]
        print("\n" + "=" * 60 + "\n--- Structured Summary ---\n" + "=" * 60)
        print(json.dumps(structured_summary, indent=2, default=str))
        print("\n" + "=" * 60 + "\n--- Narrative Summary ---\n" + "=" * 60)
        # Use ASCII-safe print for Windows consoles that don't support ₹ (U+20B9)
        safe_narrative = narrative_summary.replace("\u20b9", "Rs.")
        print(safe_narrative)
        print("=" * 60)
        assert structured_summary is not None
        assert narrative_summary is not None

    def test_run_with_minimal_inputs(self) -> None:
        """SessionSummaryBuilder runs with valid minimal behavioral and expectancy dicts."""
        behavioral = {
            "behavioral_state": "STABLE",
            "severity_score": 0.1,
            "avg_R_normal": 0.2,
            "avg_R_post": 0.15,
            "avg_win_R_normal": 0.5,
            "avg_win_R_post": 0.4,
            "avg_loss_R_normal": -0.3,
            "avg_loss_R_post": -0.35,
            "win_rate_normal": 0.6,
            "win_rate_post": 0.5,
            "R_drop_percent": 0.1,
            "win_shrink_percent": 0.2,
            "loss_expansion_percent": 0.15,
        }
        expectancy = {
            "expectancy_normal_R": 0.18,
            "expectancy_post_R": 0.12,
            "expectancy_delta_R": -0.06,
            "economic_impact_rupees": -480.0,
            "simulated_expectancy_improvement_R": 0.03,
            "simulated_rupee_improvement": 240.0,
        }
        builder = SessionSummaryBuilder(behavioral, expectancy, total_trades=20)
        result = builder.run()
        assert result["structured_summary"]["behavioral_state"] == "STABLE"
        assert result["narrative_summary"].startswith("In this session of 20 trades")
