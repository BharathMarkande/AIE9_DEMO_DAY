import pandas as pd


class RuleComplianceEngine:
    """
    Evaluates rule-based trading discipline compliance.

    Returns:
    {
      "violations": {...},
      "discipline_scores": {...}
    }
    """

    def __init__(self, df: pd.DataFrame, rules_config: dict):
        self.df = df.copy()
        self.rules = rules_config

        self.violations = {}
        self.discipline_scores = {}

    # ==========================================================
    # RULE 1 — Risk Per Trade Compliance
    # ==========================================================
    def evaluate_risk_per_trade(self):
        declared_risk = self.rules["max_risk_per_trade"]

        losses = self.df[self.df["net_pnl"] < 0]
        actual_risk = losses["net_pnl"].abs()

        breach_mask = actual_risk > declared_risk
        breach_count = breach_mask.sum()

        breach_percent = (
            breach_count / len(self.df)
            if len(self.df) > 0 else 0
        )

        self.violations["risk_breach_count"] = int(breach_count)

        # Score decreases proportionally
        risk_score = max(0, 100 * (1 - breach_percent))
        self.discipline_scores["risk_score"] = round(risk_score, 2)

    # ==========================================================
    # RULE 2 — Minimum Risk:Reward Ratio (Winning Trades)
    # ==========================================================
    def evaluate_rr_compliance(self):
        min_rr = self.rules["min_risk_to_reward_ratio"]

        winners = self.df[self.df["is_win"] == 1]

        if len(winners) == 0:
            violation_count = 0
            violation_percent = 0
        else:
            violation_mask = winners["R_proxy"] < min_rr
            violation_count = violation_mask.sum()
            violation_percent = violation_count / len(winners)

        self.violations["rr_violation_count"] = int(violation_count)

        rr_score = max(0, 100 * (1 - violation_percent))
        self.discipline_scores["rr_score"] = round(rr_score, 2)

    # ==========================================================
    # RULE 4 — Max Trades Per Day (Overtrading)
    # ==========================================================
    def evaluate_overtrading(self):
        max_trades = self.rules["max_trades_per_day"]

        trade_date = self.df["entry_time"].dt.date
        trades_per_day = self.df.groupby(trade_date).size()

        breach_days = trades_per_day[trades_per_day > max_trades]
        breach_count = len(breach_days)

        frequency = (
            breach_count / len(trades_per_day)
            if len(trades_per_day) > 0 else 0
        )

        self.violations["overtrading_days"] = int(breach_count)

        overtrading_score = max(0, 100 * (1 - frequency))
        self.discipline_scores["overtrading_score"] = round(overtrading_score, 2)

    # ==========================================================
    # RULE 5 — Max Daily Loss
    # ==========================================================
    def evaluate_daily_loss(self):
        max_daily_loss = self.rules["max_daily_loss"]

        trade_date = self.df["entry_time"].dt.date
        daily_pnl = self.df.groupby(trade_date)["net_pnl"].sum()

        breach_days = daily_pnl[daily_pnl < -max_daily_loss]
        breach_count = len(breach_days)

        frequency = (
            breach_count / len(daily_pnl)
            if len(daily_pnl) > 0 else 0
        )

        self.violations["daily_loss_breaches"] = int(breach_count)

        daily_loss_score = max(0, 100 * (1 - frequency))
        self.discipline_scores["daily_loss_score"] = round(daily_loss_score, 2)

    # ==========================================================
    # OVERALL DISCIPLINE SCORE (Risk-Weighted)
    # ==========================================================
    def compute_overall_score(self):
        """
        Risk-weighted scoring architecture.

        Capital survival rules carry more weight.
        """

        weights = {
            "risk_score": 0.35,
            "daily_loss_score": 0.30,
            "overtrading_score": 0.20,
            "rr_score": 0.15,
        }

        overall = 0

        for key, weight in weights.items():
            overall += self.discipline_scores.get(key, 100) * weight

        self.discipline_scores["overall_discipline_score"] = round(overall, 2)

    # ==========================================================
    # RUN
    # ==========================================================
    def run(self):

        self.evaluate_risk_per_trade()
        self.evaluate_rr_compliance()
        self.evaluate_overtrading()
        self.evaluate_daily_loss()

        self.compute_overall_score()

        return {
            "violations": self.violations,
            "discipline_scores": self.discipline_scores
        }