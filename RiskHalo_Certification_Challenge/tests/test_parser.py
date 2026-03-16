"""Tests for app.parser TradeParser."""

import pytest
import pandas as pd
from pathlib import Path

from app.parser import TradeParser

# Path to test trade data file (used for skipif at collection time)
TEST_TRADE_DATA_PATH = Path(__file__).resolve().parent / "data" / "test_trade_data.xlsx"


class TestTradeParser:
    """Tests for TradeParser class (uses tests/data/test_trade_data.xlsx)."""

    def test_parse_excel_returns_dataframe(self, sample_excel_path: Path) -> None:
        """Parse Excel file and verify DataFrame is returned with correct shape."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert df.head() is not None

    def test_parse_excel_has_required_columns(self, sample_excel_path: Path) -> None:
        """Parsed DataFrame has all standardized columns."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        expected_columns = [
            "trade_id", "instrument", "direction", "entry_price", "exit_price",
            "quantity", "entry_time", "exit_time", "gross_pnl", "net_pnl",
            "charges", "hold_time_minutes"
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_parse_excel_instrument_mapping(self, sample_excel_path: Path) -> None:
        """Security Name is mapped to instrument."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        assert list(df["instrument"]) == ["RELIANCE", "TCS", "INFY"]

    def test_parse_excel_direction_is_long(self, sample_excel_path: Path) -> None:
        """All trades are inferred as LONG."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        assert (df["direction"] == "LONG").all()

    def test_parse_excel_sorted_by_exit_time(self, sample_excel_path: Path) -> None:
        """Trades are sorted chronologically by exit time."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        assert df["exit_time"].is_monotonic_increasing

    def test_parse_excel_trade_id_generated(self, sample_excel_path: Path) -> None:
        """Trade IDs are unique MD5 hashes."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        assert df["trade_id"].nunique() == len(df)
        assert df["trade_id"].str.len().iloc[0] == 32  # MD5 hex length

    def test_parse_excel_hold_time_positive(self, sample_excel_path: Path) -> None:
        """Hold time in minutes is computed and non-negative."""
        parser = TradeParser(str(sample_excel_path))
        df = parser.parse()
        assert (df["hold_time_minutes"] >= 0).all()

    def test_parse_csv(self, sample_csv_path: Path) -> None:
        """Parser accepts CSV files."""
        parser = TradeParser(str(sample_csv_path))
        df = parser.parse()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

    def test_parse_nonexistent_file_raises(self) -> None:
        """Non-existent file raises ValueError."""
        parser = TradeParser("nonexistent_file.xlsx")
        with pytest.raises(ValueError, match="Error reading file"):
            parser.parse()

    def test_parse_unsupported_format_raises(self, tmp_path: Path) -> None:
        """Unsupported file format raises ValueError."""
        bad_file = tmp_path / "file.txt"
        bad_file.write_text("not excel or csv")
        parser = TradeParser(str(bad_file))
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse()

    def test_parse_missing_columns_raises(
        self, tmp_path: Path, sample_trades_df: pd.DataFrame
    ) -> None:
        """Missing required columns raises ValueError."""
        incomplete_df = sample_trades_df.drop(columns=["Security Name", "Buy Date"])
        file_path = tmp_path / "incomplete.xlsx"
        incomplete_df.to_excel(file_path, index=False)
        parser = TradeParser(str(file_path))
        with pytest.raises(ValueError, match="Missing required columns"):
            parser.parse()

    def test_parse_partial_closes_raises(
        self, tmp_path: Path, sample_trades_df: pd.DataFrame
    ) -> None:
        """Partial closes (buy_qty != sell_qty) raise ValueError."""
        sample_trades_df.loc[0, "Sell Qty"] = 50  # Partial close
        file_path = tmp_path / "partial.xlsx"
        sample_trades_df.to_excel(file_path, index=False)
        parser = TradeParser(str(file_path))
        with pytest.raises(ValueError, match="Partial closes detected"):
            parser.parse()


@pytest.mark.skipif(not TEST_TRADE_DATA_PATH.exists(), reason="tests/data/test_trade_data.xlsx not found")
class TestTradeParserDataFile:
    """Tests using tests/data/test_trade_data.xlsx."""

    def test_parse_data_trade_returns_dataframe(self, test_trade_data_path_normalized: Path | None) -> None:
        """Parse test_trade_data.xlsx and verify DataFrame is returned."""
        assert test_trade_data_path_normalized is not None
        parser = TradeParser(str(test_trade_data_path_normalized))
        df = parser.parse()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert df.head() is not None

    def test_parse_data_trade_has_required_columns(self, test_trade_data_path_normalized: Path | None) -> None:
        """Parsed data file has all standardized columns."""
        assert test_trade_data_path_normalized is not None
        parser = TradeParser(str(test_trade_data_path_normalized))
        df = parser.parse()
        expected_columns = [
            "trade_id", "instrument", "direction", "entry_price", "exit_price",
            "quantity", "entry_time", "exit_time", "gross_pnl", "net_pnl",
            "charges", "hold_time_minutes"
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_parse_data_trade_no_nulls(self, test_trade_data_path_normalized: Path | None) -> None:
        """Parsed data file has no null values."""
        assert test_trade_data_path_normalized is not None
        parser = TradeParser(str(test_trade_data_path_normalized))
        df = parser.parse()
        assert df.isnull().sum().sum() == 0

    def test_parse_data_trade_numeric_columns_valid(self, test_trade_data_path_normalized: Path | None) -> None:
        """Numeric columns have valid float types."""
        assert test_trade_data_path_normalized is not None
        parser = TradeParser(str(test_trade_data_path_normalized))
        df = parser.parse()
        numeric_cols = ["entry_price", "exit_price", "quantity", "gross_pnl", "net_pnl", "charges", "hold_time_minutes"]
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} should be numeric"

    def test_parse_data_trade_direction_and_sort(self, test_trade_data_path_normalized: Path | None) -> None:
        """All trades are LONG and sorted by exit time."""
        assert test_trade_data_path_normalized is not None
        parser = TradeParser(str(test_trade_data_path_normalized))
        df = parser.parse()
        assert (df["direction"] == "LONG").all()
        assert df["exit_time"].is_monotonic_increasing

    def test_read_and_print_trade_data_raw(self, test_trade_data_path: Path) -> None:
        """Read all columns and data from test_trade_data.xlsx and print it."""
        df = pd.read_excel(test_trade_data_path)
        df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
        print("\n--- Columns ---")
        print(list(df.columns))
        print("\n--- All Data ---")
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_rows", None)
        print(df.to_string())
