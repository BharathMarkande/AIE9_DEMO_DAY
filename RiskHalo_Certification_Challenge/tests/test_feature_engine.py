"""Tests for app.feature_engine FeatureEngine."""

import pytest
import pandas as pd
from pathlib import Path

from app.parser import TradeParser
from app.feature_engine import FeatureEngine

TEST_TRADE_DATA_PATH = Path(__file__).resolve().parent / "data" / "test_trade_data.xlsx"


class TestFeatureEngine:
    """Tests for FeatureEngine class (uses tests/data/test_trade_data.xlsx)."""

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_run_returns_dataframe_with_expected_columns(
        self, parsed_test_trade_data: pd.DataFrame | None
    ) -> None:
        """FeatureEngine.run() returns DataFrame with behavioral feature columns."""
        assert parsed_test_trade_data is not None
        engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
        feature_df = engine.run()
        assert isinstance(feature_df, pd.DataFrame)
        expected_features = [
            "trade_sequence",
            "R_proxy",
            "is_win",
            "is_loss",
            "is_breakeven",
            "loss_streak",
            "win_streak",
            "post_loss_flag",
        ]
        for col in expected_features:
            assert col in feature_df.columns, f"Missing column: {col}"

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_r_proxy_computation(self, parsed_test_trade_data: pd.DataFrame | None) -> None:
        """R_proxy = net_pnl / declared_risk."""
        assert parsed_test_trade_data is not None
        engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
        feature_df = engine.run()
        expected_r = parsed_test_trade_data["net_pnl"] / 2000
        pd.testing.assert_series_equal(
            feature_df["R_proxy"], expected_r, check_names=False
        )

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_is_win_is_loss_flags(self, parsed_test_trade_data: pd.DataFrame | None) -> None:
        """is_win=1 when net_pnl>0, is_loss=1 when net_pnl<0."""
        assert parsed_test_trade_data is not None
        engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
        feature_df = engine.run()
        assert (feature_df["is_win"] == (parsed_test_trade_data["net_pnl"] > 0).astype(int)).all()
        assert (feature_df["is_loss"] == (parsed_test_trade_data["net_pnl"] < 0).astype(int)).all()

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_trade_sequence(self, parsed_test_trade_data: pd.DataFrame | None) -> None:
        """trade_sequence is 1, 2, 3, ..."""
        assert parsed_test_trade_data is not None
        engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
        feature_df = engine.run()
        expected = list(range(1, len(parsed_test_trade_data) + 1))
        assert list(feature_df["trade_sequence"]) == expected

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_post_loss_flag_first_trade_zero(self, parsed_test_trade_data: pd.DataFrame | None) -> None:
        """First trade has post_loss_flag=0 (no previous trade)."""
        assert parsed_test_trade_data is not None
        engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
        feature_df = engine.run()
        assert feature_df["post_loss_flag"].iloc[0] == 0

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_declared_risk_must_be_positive(self, parsed_test_trade_data: pd.DataFrame | None) -> None:
        """FeatureEngine raises ValueError when declared_risk <= 0."""
        assert parsed_test_trade_data is not None
        with pytest.raises(ValueError, match="Declared risk per trade must be positive"):
            FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=0)
        with pytest.raises(ValueError, match="Declared risk per trade must be positive"):
            FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=-100)

    def test_loss_streak_logic(self) -> None:
        """loss_streak: Loss, Loss, Win, Loss -> 1, 2, 0, 1."""
        # Build minimal parsed df with Loss, Loss, Win, Loss pattern
        df = pd.DataFrame({
            "trade_id": ["a", "b", "c", "d"],
            "instrument": ["X", "X", "X", "X"],
            "direction": ["LONG"] * 4,
            "entry_price": [100.0] * 4,
            "exit_price": [100.0] * 4,
            "quantity": [10] * 4,
            "entry_time": pd.to_datetime(["2024-01-01 09:00", "2024-01-02 09:00", "2024-01-03 09:00", "2024-01-04 09:00"]),
            "exit_time": pd.to_datetime(["2024-01-01 10:00", "2024-01-02 10:00", "2024-01-03 10:00", "2024-01-04 10:00"]),
            "gross_pnl": [-100, -200, 150, -50],
            "net_pnl": [-100, -200, 150, -50],
            "charges": [0.0] * 4,
            "hold_time_minutes": [60.0] * 4,
        })
        engine = FeatureEngine(df, declared_risk_per_trade=100)
        feature_df = engine.run()
        assert list(feature_df["loss_streak"]) == [1, 2, 0, 1]

    def test_win_streak_logic(self) -> None:
        """win_streak: Win, Win, Loss, Win -> 1, 2, 0, 1."""
        df = pd.DataFrame({
            "trade_id": ["a", "b", "c", "d"],
            "instrument": ["X"] * 4,
            "direction": ["LONG"] * 4,
            "entry_price": [100.0] * 4,
            "exit_price": [100.0] * 4,
            "quantity": [10] * 4,
            "entry_time": pd.to_datetime(["2024-01-01 09:00", "2024-01-02 09:00", "2024-01-03 09:00", "2024-01-04 09:00"]),
            "exit_time": pd.to_datetime(["2024-01-01 10:00", "2024-01-02 10:00", "2024-01-03 10:00", "2024-01-04 10:00"]),
            "gross_pnl": [100, 200, -150, 50],
            "net_pnl": [100, 200, -150, 50],
            "charges": [0.0] * 4,
            "hold_time_minutes": [60.0] * 4,
        })
        engine = FeatureEngine(df, declared_risk_per_trade=100)
        feature_df = engine.run()
        assert list(feature_df["win_streak"]) == [1, 2, 0, 1]

    def test_post_loss_flag_logic(self) -> None:
        """post_loss_flag = 1 when previous trade was a loss."""
        # Loss, Win, Loss -> post_loss: 0, 1, 0
        df = pd.DataFrame({
            "trade_id": ["a", "b", "c"],
            "instrument": ["X"] * 3,
            "direction": ["LONG"] * 3,
            "entry_price": [100.0] * 3,
            "exit_price": [100.0] * 3,
            "quantity": [10] * 3,
            "entry_time": pd.to_datetime(["2024-01-01 09:00", "2024-01-02 09:00", "2024-01-03 09:00"]),
            "exit_time": pd.to_datetime(["2024-01-01 10:00", "2024-01-02 10:00", "2024-01-03 10:00"]),
            "gross_pnl": [-100, 150, -50],
            "net_pnl": [-100, 150, -50],
            "charges": [0.0] * 3,
            "hold_time_minutes": [60.0] * 3,
        })
        engine = FeatureEngine(df, declared_risk_per_trade=100)
        feature_df = engine.run()
        assert list(feature_df["post_loss_flag"]) == [0, 1, 0]

    @pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
    def test_integration_parser_feature_engine(
        self, parsed_test_trade_data: pd.DataFrame | None
    ) -> None:
        """Integration: Parse trades from test_trade_data.xlsx, run FeatureEngine, verify output shape."""
        assert parsed_test_trade_data is not None
        df = parsed_test_trade_data
        declared_risk = 2000
        engine = FeatureEngine(df, declared_risk)
        feature_df = engine.run()
        display_cols = [
            "trade_sequence",
            "net_pnl",
            "R_proxy",
            "is_win",
            "loss_streak",
            "win_streak",
            "post_loss_flag",
        ]
        for col in display_cols:
            assert col in feature_df.columns
        assert len(feature_df) == len(df)
        # Sanity: head(10) is accessible (sample may have < 10 rows)
        _ = feature_df[display_cols].head(10)
