import pandas as pd
import hashlib
import os


class TradeParser:
    """
    Parses broker CSV export into RiskHalo standardized schema.
    Designed for intraday trades (buy and sell same day).
    """

    REQUIRED_COLUMNS = [
        "Security Name",
        "Buy Date",
        "Buy Qty",
        "Avg Buy Price",
        "Sell Date",
        "Sell Qty",
        "Avg Sell Price",
        "Gross P&L",
        "Total Charges",
        "Net P&L"
    ]

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    # --------------------------------------------------
    # Load File (Excel or CSV)
    # --------------------------------------------------
    def load_file(self):
        try:
            file_extension = os.path.splitext(self.file_path)[1].lower()

            if file_extension in [".xlsx", ".xls"]:
                self.df = pd.read_excel(self.file_path)
            elif file_extension == ".csv":
                self.df = pd.read_csv(self.file_path)
            else:
                raise ValueError("Unsupported file format. Please upload CSV or Excel file.")

        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

        return self.df

    # --------------------------------------------------
    # Validate Required Columns
    # --------------------------------------------------
    def validate_columns(self):
        missing = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        return True

    # --------------------------------------------------
    # Standardize Schema
    # --------------------------------------------------
    def standardize_schema(self):
        self.df.rename(columns={
            "Security Name": "instrument",
            "Buy Date": "entry_time",
            "Sell Date": "exit_time",
            "Buy Qty": "buy_qty",
            "Sell Qty": "sell_qty",
            "Avg Buy Price": "entry_price",
            "Avg Sell Price": "exit_price",
            "Gross P&L": "gross_pnl",
            "Net P&L": "net_pnl",
            "Total Charges": "charges"
        }, inplace=True)

        return self.df

    # --------------------------------------------------
    # Validate Quantities (No Partial Closes in MVP)
    # --------------------------------------------------
    def validate_quantities(self):
        if not (self.df["buy_qty"] == self.df["sell_qty"]).all():
            raise ValueError("Partial closes detected. MVP does not support partial positions.")

        self.df["quantity"] = self.df["buy_qty"]
        return self.df

    # --------------------------------------------------
    # Convert Data Types
    # --------------------------------------------------
    def convert_dtypes(self):

        numeric_cols = [
            "entry_price",
            "exit_price",
            "quantity",
            "gross_pnl",
            "net_pnl",
            "charges"
        ]

        for col in numeric_cols:
            self.df[col] = (
                self.df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .astype(float)
            )

        # Convert dates (supports dd-mm-yyyy, yyyy-mm-dd, and datetime strings)
        self.df["entry_time"] = pd.to_datetime(
            self.df["entry_time"], format="mixed", dayfirst=True
        )
        self.df["exit_time"] = pd.to_datetime(
            self.df["exit_time"], format="mixed", dayfirst=True
        )

        # Sort chronologically by exit date
        self.df = self.df.sort_values("exit_time").reset_index(drop=True)

        return self.df

    # --------------------------------------------------
    # Infer Direction (Long-only for MVP)
    # --------------------------------------------------
    def infer_direction(self):
        self.df["direction"] = "LONG"
        return self.df

    # --------------------------------------------------
    # Compute Holding Time
    # --------------------------------------------------
    def compute_hold_time(self):

        self.df["hold_time_minutes"] = (
            (self.df["exit_time"] - self.df["entry_time"])
            .dt.total_seconds() / 60
        )

        if (self.df["hold_time_minutes"] < 0).any():
            raise ValueError("Negative holding period detected. Check dates.")

        return self.df

    # --------------------------------------------------
    # Generate Trade ID
    # --------------------------------------------------
    def generate_trade_id(self):

        def create_hash(row):
            unique_string = f"{row['instrument']}_{row['entry_time']}_{row['quantity']}"
            return hashlib.md5(unique_string.encode()).hexdigest()

        self.df["trade_id"] = self.df.apply(create_hash, axis=1)
        return self.df

    # --------------------------------------------------
    # Final Column Ordering
    # --------------------------------------------------
    def reorder_columns(self):

        ordered_columns = [
            "trade_id",
            "instrument",
            "direction",
            "entry_price",
            "exit_price",
            "quantity",
            "entry_time",
            "exit_time",
            "gross_pnl",
            "net_pnl",
            "charges",
            "hold_time_minutes"
        ]

        self.df = self.df[ordered_columns]
        return self.df

    # --------------------------------------------------
    # Main Parse Method
    # --------------------------------------------------
    def parse(self):

        self.load_file()
        self.validate_columns()
        self.standardize_schema()
        self.validate_quantities()
        self.convert_dtypes()
        self.infer_direction()
        self.compute_hold_time()
        self.generate_trade_id()
        self.reorder_columns()

        # Final safety check
        if self.df.isnull().sum().sum() > 0:
            raise ValueError("Null values detected after parsing.")

        return self.df
