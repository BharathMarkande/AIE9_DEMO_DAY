"""Tests for app.behavioral_engine BehavioralEngine."""

import pytest
import pandas as pd
from pathlib import Path

from app.feature_engine import FeatureEngine
from app.behavioral_engine import BehavioralEngine

TEST_TRADE_DATA_PATH = Path(__file__).resolve().parent / "data" / "test_trade_data.xlsx"


class TestBehavioralEngine:
    """Tests for BehavioralEngine class (uses tests/data/test_trade_data.xlsx)."""

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_run_returns_expected_dict_keys(self, feature_test_trade_data: pd.DataFrame | None) -> None:
        """BehavioralEngine.run() returns dict with all expected keys."""
        assert feature_test_trade_data is not None
        engine = BehavioralEngine(feature_test_trade_data)
        result = engine.run()
        assert isinstance(result, dict)
        expected_keys = [
            "behavioral_state",
            "severity_score",
            "avg_R_normal",
            "avg_R_post",
            "avg_win_R_normal",
            "avg_win_R_post",
            "avg_loss_R_normal",
            "avg_loss_R_post",
            "win_rate_normal",
            "win_rate_post",
            "R_drop_percent",
            "win_shrink_percent",
            "loss_expansion_percent",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_behavioral_state_valid(self, feature_test_trade_data: pd.DataFrame | None) -> None:
        """behavioral_state is one of the four valid states."""
        assert feature_test_trade_data is not None
        engine = BehavioralEngine(feature_test_trade_data)
        result = engine.run()
        valid_states = {"STABLE", "CONFIDENCE_CONTRACTION", "LOSS_ESCALATION", "ADAPTIVE_RECOVERY"}
        assert result["behavioral_state"] in valid_states

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_severity_score_range(self, feature_test_trade_data: pd.DataFrame | None) -> None:
        """severity_score is between 0 and 1 inclusive."""
        assert feature_test_trade_data is not None
        engine = BehavioralEngine(feature_test_trade_data)
        result = engine.run()
        assert 0 <= result["severity_score"] <= 1

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_win_rates_in_range(self, feature_test_trade_data: pd.DataFrame | None) -> None:
        """win_rate_normal and win_rate_post are between 0 and 1."""
        assert feature_test_trade_data is not None
        engine = BehavioralEngine(feature_test_trade_data)
        result = engine.run()
        assert 0 <= result["win_rate_normal"] <= 1
        assert 0 <= result["win_rate_post"] <= 1

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_group_sizes_meet_minimum(self, feature_test_trade_data: pd.DataFrame | None) -> None:
        """Both normal and post-loss groups have at least 3 trades."""
        assert feature_test_trade_data is not None
        normal_count = (feature_test_trade_data["post_loss_flag"] == 0).sum()
        post_count = (feature_test_trade_data["post_loss_flag"] == 1).sum()
        assert normal_count >= 3, "Need at least 3 normal trades for BehavioralEngine"
        assert post_count >= 3, "Need at least 3 post-loss trades for BehavioralEngine"

    def test_requires_post_loss_flag(self) -> None:
        """BehavioralEngine raises ValueError when post_loss_flag column is missing."""
        df = pd.DataFrame({
            "net_pnl": [100, -50, 75],
            "R_proxy": [0.5, -0.25, 0.375],
        })
        with pytest.raises(ValueError, match="FeatureEngine must be run before BehavioralEngine"):
            BehavioralEngine(df)

    def test_requires_minimum_group_size(self) -> None:
        """BehavioralEngine raises ValueError when one group has < 3 trades."""
        # Build df with only 2 post-loss trades
        df = pd.DataFrame({
            "trade_id": ["a"] * 6,
            "instrument": ["X"] * 6,
            "R_proxy": [0.5, 0.3, -0.2, 0.4, -0.1, 0.2],  # post_loss: 0,0,1,0,1,0 -> 2 post-loss
            "post_loss_flag": [0, 0, 1, 0, 1, 0],
        })
        with pytest.raises(ValueError, match="Not enough trades in one of the groups"):
            engine = BehavioralEngine(df)
            engine.run()

    def test_split_groups_logic(self) -> None:
        """normal_df has post_loss_flag=0, post_df has post_loss_flag=1."""
        df = pd.DataFrame({
            "trade_id": ["a"] * 8,
            "instrument": ["X"] * 8,
            "R_proxy": [0.5, -0.2, 0.3, -0.1, 0.4, -0.3, 0.2, -0.2],
            "post_loss_flag": [0, 0, 1, 0, 1, 0, 1, 0],  # 5 normal, 3 post
        })
        engine = BehavioralEngine(df)
        engine.split_groups()
        assert (engine.normal_df["post_loss_flag"] == 0).all()
        assert (engine.post_df["post_loss_flag"] == 1).all()
        assert len(engine.normal_df) == 5
        assert len(engine.post_df) == 3

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_integration_parser_feature_behavioral(
        self, parsed_test_trade_data: pd.DataFrame | None
    ) -> None:
        """Integration: Parse -> FeatureEngine -> BehavioralEngine full pipeline."""
        assert parsed_test_trade_data is not None
        feature_engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
        feature_df = feature_engine.run()
        behavioral_engine = BehavioralEngine(feature_df)
        result = behavioral_engine.run()
        assert "behavioral_state" in result
        assert "severity_score" in result
        assert isinstance(result["avg_R_normal"], (int, float))
        assert isinstance(result["avg_R_post"], (int, float))
