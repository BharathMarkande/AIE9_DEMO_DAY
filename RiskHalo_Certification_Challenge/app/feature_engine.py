import pandas as pd


class FeatureEngine:
    """
    Converts normalized trades into behavioral signals.
    """

    def __init__(self, df: pd.DataFrame, declared_risk_per_trade: float):
        self.df = df.copy()
        self.declared_risk = declared_risk_per_trade

        if self.declared_risk <= 0:
            raise ValueError("Declared risk per trade must be positive.")

    # --------------------------------------------------
    # Compute R Proxy
    # --------------------------------------------------
    def compute_r_proxy(self):
        """
        Computes R-multiple for each trade.

        R_proxy = net_pnl / declared_risk_per_trade.
        This normalizes performance relative to intended risk (e.g., -4000 PnL with ₹2000 risk = -2R).

        R_proxy allows behavioral consistency to be measured independent of capital size.
        """

        self.df["R_proxy"] = self.df["net_pnl"] / self.declared_risk
        return self.df

    # --------------------------------------------------
    # Win / Loss Flags
    # --------------------------------------------------
    def compute_outcome_flags(self):
        """
        Generates binary outcome indicators.

        is_win = 1 if net_pnl > 0
        is_loss = 1 if net_pnl < 0
        is_breakeven = 1 if net_pnl == 0

        These flags enable win rate calculation, streak detection, and expectancy analysis.
        """

        self.df["is_win"] = (self.df["net_pnl"] > 0).astype(int)
        self.df["is_loss"] = (self.df["net_pnl"] < 0).astype(int)
        self.df["is_breakeven"] = (self.df["net_pnl"] == 0).astype(int)

        return self.df

    # --------------------------------------------------
    # Trade Sequence Number
    # --------------------------------------------------
    def compute_trade_sequence(self):
        """
        Assigns sequential order to trades.

        trade_sequence = 1, 2, 3, ...
        Preserves chronological structure required for streak detection and post-loss segmentation.

        Behavioral modeling depends on correct trade ordering.
        """

        self.df = self.df.reset_index(drop=True)
        self.df["trade_sequence"] = self.df.index + 1

        return self.df

    # --------------------------------------------------
    # Loss Streak Count
    # --------------------------------------------------
    def compute_loss_streak(self):
        """
        Computes consecutive loss count.

        If trades are: Loss, Loss, Win, Loss
        loss_streak becomes: 1, 2, 0, 1

        Loss streak serves as a proxy for emotional pressure buildup during drawdowns.
        """

        loss_streak = []
        current_streak = 0

        for _, row in self.df.iterrows():
            if row["is_loss"] == 1:
                current_streak += 1
            else:
                current_streak = 0

            loss_streak.append(current_streak)

        self.df["loss_streak"] = loss_streak
        return self.df

    # --------------------------------------------------
    # Win Streak Count
    # --------------------------------------------------
    def compute_win_streak(self):
        """
        Computes consecutive win count.

        If trades are: Win, Win, Loss, Win
        win_streak becomes: 1, 2, 0, 1

        Win streaks help detect overconfidence-driven risk expansion.
        """

        win_streak = []
        current_streak = 0

        for _, row in self.df.iterrows():
            if row["is_win"] == 1:
                current_streak += 1
            else:
                current_streak = 0

            win_streak.append(current_streak)

        self.df["win_streak"] = win_streak
        return self.df

    # --------------------------------------------------
    # Post-Loss Flag
    # --------------------------------------------------
    def compute_post_loss_flag(self):
        """
        Flags trades occurring immediately after a loss.

        post_loss_flag = 1 if previous trade was a loss.
        Example: Loss → Win → Loss
		         0       1      0

        This variable segments trades into neutral vs emotionally reactive states.
        """

        post_loss_flag = []

        for i in range(len(self.df)):
            if i == 0:
                post_loss_flag.append(0)
            else:
                previous_trade_loss = self.df.loc[i - 1, "is_loss"]
                post_loss_flag.append(previous_trade_loss)

        self.df["post_loss_flag"] = post_loss_flag
        return self.df

    # --------------------------------------------------
    # Run Full Pipeline
    # --------------------------------------------------
    def run(self):
        """
        Executes full behavioral feature pipeline.

        Transforms normalized trades into psychological indicators
        (R-multiples, streaks, and post-loss state flags).

        Output is a behavior-ready dataset used by the Behavioral Engine.
        """

        self.compute_r_proxy()
        self.compute_outcome_flags()
        self.compute_trade_sequence()
        self.compute_loss_streak()
        self.compute_win_streak()
        self.compute_post_loss_flag()

        return self.df