"""Pytest fixtures for RiskHalo tests."""

import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture
def sample_trades_df() -> pd.DataFrame:
    """Sample trade data with all required columns in broker format."""
    return pd.DataFrame({
        "Security Name": ["RELIANCE", "TCS", "INFY"],
        "Buy Date": ["2024-01-15 09:30", "2024-01-15 10:15", "2024-01-15 11:00"],
        "Buy Qty": [100, 50, 75],
        "Avg Buy Price": [2500.50, 3500.00, 1500.25],
        "Sell Date": ["2024-01-15 10:00", "2024-01-15 11:00", "2024-01-15 11:45"],
        "Sell Qty": [100, 50, 75],
        "Avg Sell Price": [2520.00, 3480.00, 1510.00],
        "Gross P&L": [1950.00, -1000.00, 731.25],
        "Total Charges": [20.50, 15.00, 18.75],
        "Net P&L": [1929.50, -1015.00, 712.50],
    })


@pytest.fixture
def sample_excel_path(tmp_path: Path, sample_trades_df: pd.DataFrame) -> Path:
    """Create a temporary Excel file with sample trade data."""
    file_path = tmp_path / "sample_trades.xlsx"
    sample_trades_df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_csv_path(tmp_path: Path, sample_trades_df: pd.DataFrame) -> Path:
    """Create a temporary CSV file with sample trade data."""
    file_path = tmp_path / "sample_trades.csv"
    sample_trades_df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def parsed_trades_df(sample_excel_path: Path) -> pd.DataFrame:
    """Parsed trades from sample Excel (parser output format)."""
    from app.parser import TradeParser
    parser = TradeParser(str(sample_excel_path))
    return parser.parse()


@pytest.fixture
def test_trade_data_path() -> Path:
    """Path to tests/data/test_trade_data.xlsx."""
    return Path(__file__).resolve().parent / "data" / "test_trade_data.xlsx"


def _normalize_trade_excel(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """Drop Unnamed columns and map broker column variants."""
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    return df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})


_COLUMN_MAP = {
    "Buy Qty": "Buy Qty",
    "Avg Buy Price": "Avg Buy Price",
    "Sell Qty": "Sell Qty",
    "Avg Sell Price": "Avg Sell Price",
}


@pytest.fixture
def test_trade_data_path_normalized(test_trade_data_path: Path, tmp_path: Path) -> Path | None:
    """
    Normalized copy of tests/data/test_trade_data.xlsx with parser-expected column names.
    Returns None if source file does not exist.
    """
    if not test_trade_data_path.exists():
        return None
    df = pd.read_excel(test_trade_data_path)
    df = _normalize_trade_excel(df, _COLUMN_MAP)
    out_path = tmp_path / "test_trade_normalized.xlsx"
    df.to_excel(out_path, index=False)
    return out_path


@pytest.fixture
def parsed_test_trade_data(test_trade_data_path_normalized: Path | None) -> pd.DataFrame | None:
    """
    Parsed trades from tests/data/test_trade_data.xlsx.
    Returns None if file does not exist.
    """
    if test_trade_data_path_normalized is None:
        return None
    from app.parser import TradeParser
    return TradeParser(str(test_trade_data_path_normalized)).parse()


@pytest.fixture
def feature_test_trade_data(parsed_test_trade_data: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    Feature-engine output from tests/data/test_trade_data.xlsx.
    Returns None if source file does not exist.
    """
    if parsed_test_trade_data is None:
        return None
    from app.feature_engine import FeatureEngine
    engine = FeatureEngine(parsed_test_trade_data, declared_risk_per_trade=2000)
    return engine.run()


@pytest.fixture
def behavioral_test_trade_data(feature_test_trade_data: pd.DataFrame | None) -> dict | None:
    """
    Behavioral-engine output from tests/data/test_trade_data.xlsx.
    Returns None if source file does not exist.
    """
    if feature_test_trade_data is None:
        return None
    from app.behavioral_engine import BehavioralEngine
    engine = BehavioralEngine(feature_test_trade_data)
    return engine.run()


@pytest.fixture
def expectancy_test_trade_data(
    behavioral_test_trade_data: dict | None, feature_test_trade_data
) -> dict | None:
    """
    Expectancy-engine output from tests/data/test_trade_data.xlsx.
    Returns None if source file does not exist.
    """
    if behavioral_test_trade_data is None or feature_test_trade_data is None:
        return None
    from app.expectancy_engine import ExpectancyEngine
    total_trades = len(feature_test_trade_data)
    engine = ExpectancyEngine(
        behavioral_test_trade_data,
        declared_risk_per_trade=2000,
        total_trades=total_trades,
    )
    return engine.run()


@pytest.fixture
def trade_data_path() -> Path:
    """Path to data/Trade.xlsx (project data file)."""
    return Path(__file__).resolve().parent.parent / "data" / "Trade.xlsx"


@pytest.fixture
def trade_data_path_normalized(trade_data_path: Path, tmp_path: Path) -> Path | None:
    """
    Normalized copy of data/Trade.xlsx with parser-expected column names.
    Returns None if source file does not exist.
    """
    if not trade_data_path.exists():
        return None
    df = pd.read_excel(trade_data_path)
    df = _normalize_trade_excel(df, _COLUMN_MAP)
    out_path = tmp_path / "trade_normalized.xlsx"
    df.to_excel(out_path, index=False)
    return out_path
