"""Tests for app.expectancy_engine ExpectancyEngine."""

import pytest
from pathlib import Path

from app.feature_engine import FeatureEngine
from app.behavioral_engine import BehavioralEngine
from app.expectancy_engine import ExpectancyEngine

TEST_TRADE_DATA_PATH = Path(__file__).resolve().parent / "data" / "test_trade_data.xlsx"


class TestExpectancyEngine:
    """Tests for ExpectancyEngine class (uses tests/data/test_trade_data.xlsx)."""

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_run_returns_expected_dict_keys(
        self, behavioral_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """ExpectancyEngine.run() returns dict with all expected keys."""
        assert behavioral_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        engine = ExpectancyEngine(
            behavioral_test_trade_data,
            declared_risk_per_trade=2000,
            total_trades=total_trades,
        )
        result = engine.run()
        assert isinstance(result, dict)
        expected_keys = [
            "expectancy_normal_R",
            "expectancy_post_R",
            "expectancy_delta_R",
            "economic_impact_rupees",
            "simulated_expectancy_improvement_R",
            "simulated_rupee_improvement",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_expectancy_formula(
        self, behavioral_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """Expectancy = (win_rate * avg_win_R) + (loss_rate * avg_loss_R)."""
        assert behavioral_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        engine = ExpectancyEngine(
            behavioral_test_trade_data,
            declared_risk_per_trade=2000,
            total_trades=total_trades,
        )
        result = engine.run()
        b = behavioral_test_trade_data
        expected_normal = (
            b["win_rate_normal"] * b["avg_win_R_normal"]
            + (1 - b["win_rate_normal"]) * b["avg_loss_R_normal"]
        )
        expected_post = (
            b["win_rate_post"] * b["avg_win_R_post"]
            + (1 - b["win_rate_post"]) * b["avg_loss_R_post"]
        )
        assert abs(result["expectancy_normal_R"] - round(expected_normal, 3)) < 0.001
        assert abs(result["expectancy_post_R"] - round(expected_post, 3)) < 0.001

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_expectancy_delta(
        self, behavioral_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """expectancy_delta_R = expectancy_post - expectancy_normal."""
        assert behavioral_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        engine = ExpectancyEngine(
            behavioral_test_trade_data,
            declared_risk_per_trade=2000,
            total_trades=total_trades,
        )
        result = engine.run()
        expected_delta = result["expectancy_post_R"] - result["expectancy_normal_R"]
        assert abs(result["expectancy_delta_R"] - expected_delta) < 0.001

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_economic_impact_uses_declared_risk(
        self, behavioral_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """economic_impact_rupees scales with declared_risk and total_trades."""
        assert behavioral_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        engine1 = ExpectancyEngine(
            behavioral_test_trade_data,
            declared_risk_per_trade=2000,
            total_trades=total_trades,
        )
        result1 = engine1.run()
        engine2 = ExpectancyEngine(
            behavioral_test_trade_data,
            declared_risk_per_trade=4000,
            total_trades=total_trades,
        )
        result2 = engine2.run()
        assert result1["expectancy_delta_R"] == result2["expectancy_delta_R"]
        assert abs(result2["economic_impact_rupees"] - 2 * result1["economic_impact_rupees"]) < 0.01

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_simulated_improvement_non_negative(
        self, behavioral_test_trade_data: dict | None, feature_test_trade_data
    ) -> None:
        """simulated_expectancy_improvement_R and simulated_rupee_improvement are non-negative."""
        assert behavioral_test_trade_data is not None
        assert feature_test_trade_data is not None
        total_trades = len(feature_test_trade_data)
        engine = ExpectancyEngine(
            behavioral_test_trade_data,
            declared_risk_per_trade=2000,
            total_trades=total_trades,
        )
        result = engine.run()
        assert result["simulated_expectancy_improvement_R"] >= 0
        assert result["simulated_rupee_improvement"] >= 0

    def test_expectancy_with_minimal_behavioral_output(self) -> None:
        """ExpectancyEngine runs with valid minimal behavioral dict."""
        behavioral_output = {
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
        engine = ExpectancyEngine(
            behavioral_output,
            declared_risk_per_trade=1000,
            total_trades=20,
        )
        result = engine.run()
        assert "expectancy_normal_R" in result
        assert "expectancy_post_R" in result
        assert "expectancy_delta_R" in result
        assert "economic_impact_rupees" in result

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_integration_parser_feature_behavioral_expectancy(
        self, parsed_test_trade_data, feature_test_trade_data
    ) -> None:
        """Integration: Parse -> FeatureEngine -> BehavioralEngine -> ExpectancyEngine."""
        assert parsed_test_trade_data is not None
        assert feature_test_trade_data is not None
        behavioral_engine = BehavioralEngine(feature_test_trade_data)
        behavioral_output = behavioral_engine.run()
        total_trades = len(feature_test_trade_data)
        expectancy_engine = ExpectancyEngine(
            behavioral_output,
            declared_risk_per_trade=2000,
            total_trades=total_trades,
        )
        result = expectancy_engine.run()
        assert "expectancy_normal_R" in result
        assert "expectancy_post_R" in result
        assert "economic_impact_rupees" in result
        assert isinstance(result["expectancy_delta_R"], (int, float))
        assert isinstance(result["simulated_rupee_improvement"], (int, float))
