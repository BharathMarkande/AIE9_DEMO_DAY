class ExpectancyEngine:
    """
    Converts behavioral distortion into expectancy shifts
    and quantifies financial impact.

    This layer translates psychological inconsistency into economic cost.
    """

    def __init__(self, behavioral_output: dict, declared_risk_per_trade: float, total_trades: int, post_loss_trade_count: int):
        self.behavior = behavioral_output
        self.declared_risk = declared_risk_per_trade
        self.total_trades = total_trades
        self.post_loss_trade_count = post_loss_trade_count

    # --------------------------------------------------
    # Compute Expectancy
    # --------------------------------------------------
    def compute_expectancy(self):
        """
        Computes expectancy for normal and post-loss states.

        Expectancy (R) = (Win Rate x Avg Win R) + (Loss Rate x Avg Loss R)

        This measures the average R-multiple earned per trade
        under neutral conditions versus emotionally reactive conditions.

        The difference (expectancy_delta) reflects behavioral edge erosion.
        """

        # --- Normal Expectancy ---
        win_rate_normal = self.behavior["win_rate_normal"]
        avg_win_normal = self.behavior["avg_win_R_normal"]
        avg_loss_normal = self.behavior["avg_loss_R_normal"]

        # --- Post-Loss Expectancy ---
        win_rate_post = self.behavior["win_rate_post"]
        avg_win_post = self.behavior["avg_win_R_post"]
        avg_loss_post = self.behavior["avg_loss_R_post"]

        # --- Calculate Rates ---
        loss_rate_normal = 1 - win_rate_normal
        loss_rate_post = 1 - win_rate_post

        self.expectancy_normal = (
            win_rate_normal * avg_win_normal +
            loss_rate_normal * avg_loss_normal
        )

        self.expectancy_post = (
            win_rate_post * avg_win_post +
            loss_rate_post * avg_loss_post
        )

        self.expectancy_delta = self.expectancy_post - self.expectancy_normal
        return self.expectancy_normal, self.expectancy_post, self.expectancy_delta

    # --------------------------------------------------
    # Convert to Financial Impact
    # --------------------------------------------------
    def compute_financial_impact(self):
        """
        Converts expectancy deterioration into estimated monetary impact.

        expectancy_delta (R) x declared_risk_per_trade → rupee change per trade.

        This provides a practical estimate of how much capital
        behavioral distortion costs over the analyzed period.

        The estimate scales by total trades to approximate cumulative impact.
        """

        # Expectancy difference per trade (₹)
        rupee_delta_per_trade = self.expectancy_delta * self.declared_risk

        # Apply Delta Only to Post-Loss Trades, Expectancy shift only applies to post-loss trades
        self.economic_impact = rupee_delta_per_trade * self.post_loss_trade_count


    # --------------------------------------------------
    # Run Full Expectancy Analysi
    # --------------------------------------------------
    def run(self):
        """
        Executes full financial impact analysis pipeline:

        1. Compute expectancy in normal and post-loss states
        2. Measure expectancy delta (behavioral cost)
        3. Convert R-delta into rupee impact
        4. Simulate guardrail-based improvement

        Returns structured impact metrics used in session summaries
        and downstream reasoning layers.
        """

        self.compute_expectancy()
        self.compute_financial_impact()

        return {
            "expectancy_normal_R": round(self.expectancy_normal, 2),
            "expectancy_post_R": round(self.expectancy_post, 2),
            "expectancy_delta_R": round(self.expectancy_delta, 2),
            "economic_impact_rupees": round(self.economic_impact, 2),
            "risk_per_trade": self.declared_risk,
            "post_loss_trade_count": self.post_loss_trade_count
        }

# --------------------------------------------------
# Human-Friendly Readable Formatter
# --------------------------------------------------
def format_expectancy_summary(
    expectancy_normal_R: float,
    expectancy_post_R: float,
    expectancy_delta_R: float,
    economic_impact_rupees: float,
    behavioral_state: str,
    risk_per_trade: float = None
) -> str:
    """
    Formats expectancy metrics into a clean, human-readable summary.
    """

    # Round values for display
    normal_R = round(expectancy_normal_R, 2)
    post_R = round(expectancy_post_R, 2)
    delta_R = round(expectancy_delta_R, 2)
    impact_rupees = round(economic_impact_rupees)

    # Optional rupee conversion per trade
    if risk_per_trade:
        normal_rupees = round(normal_R * risk_per_trade)
        post_rupees = round(post_R * risk_per_trade)
        delta_rupees = round(delta_R * risk_per_trade)

        # --------------------------------------------------
    # INSUFFICIENT DATA
    # --------------------------------------------------
    if behavioral_state == "INSUFFICIENT_POST_LOSS_DATA":
        return (
            "Performance Impact\n"
            "There were insufficient post-loss trades to evaluate behavioral expectancy shift.\n"
            "Expectancy comparison requires comparable trade groups.\n"
            "No economic impact is inferred for this period."
        )

    # --------------------------------------------------
    # STABLE
    # --------------------------------------------------
    if behavioral_state == "STABLE":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"Your average trade outcome remained consistent at approximately ₹{normal_rupees} per trade.\n"
                "There is no meaningful performance deterioration after losses.\n"
                "Financial impact from behavioral distortion appears minimal."
            )
        else:
            return (
                "Performance Impact\n"
                f"Your average trade outcome remained consistent at {normal_R}R per trade.\n"
                "There is no meaningful performance deterioration after losses."
            )

    # --------------------------------------------------
    # LOSS_ESCALATION
    # --------------------------------------------------
    if behavioral_state == "LOSS_ESCALATION":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"In stable conditions, your trades averaged ₹{normal_rupees} per trade.\n"
                f"After a loss, performance declined to an average loss of ₹{abs(post_rupees)} per trade.\n"
                f"This deterioration reflects post-loss loss escalation behavior.\n"
                f"Across the analyzed period, this behavioral shift reduced performance by approximately ₹{abs(impact_rupees)}."
            )
        else:
            return (
                "Performance Impact\n"
                f"Normal trades averaged {normal_R}R per trade.\n"
                f"After losses, trades averaged {post_R}R per trade.\n"
                f"This deterioration reflects post-loss loss escalation behavior.\n"
                f"Estimated impact over period: ₹{abs(impact_rupees)}."
            )

    # --------------------------------------------------
    # CONFIDENCE_CONTRACTION
    # --------------------------------------------------
    if behavioral_state == "CONFIDENCE_CONTRACTION":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"Baseline performance averaged ₹{normal_rupees} per trade.\n"
                f"After losses, profitability declined to ₹{post_rupees} per trade.\n"
                "This suggests profit compression rather than risk expansion.\n"
                f"The resulting expectancy shift impacted performance by approximately ₹{abs(impact_rupees)}."
            )
        else:
            return (
                "Performance Impact\n"
                f"Baseline performance averaged {normal_R}R per trade.\n"
                f"After losses, performance shifted to {post_R}R per trade.\n"
                "This suggests profit compression following losses."
            )

    # --------------------------------------------------
    # ADAPTIVE_RECOVERY
    # --------------------------------------------------
    if behavioral_state == "ADAPTIVE_RECOVERY":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"In stable conditions, trades averaged ₹{normal_rupees} per trade.\n"
                f"After losses, performance improved to approximately ₹{post_rupees} per trade.\n"
                "This indicates constructive behavioral adjustment rather than emotional distortion.\n"
                f"The positive shift contributed approximately ₹{abs(impact_rupees)} over the period."
            )
        else:
            return (
                "Performance Impact\n"
                f"Normal trades averaged {normal_R}R per trade.\n"
                f"After losses, trades improved to {post_R}R per trade.\n"
                "This indicates adaptive recovery behavior."
            )
            
            
    return (
            "Performance Impact\n"
            f"Normal trades: {normal_R}R per trade\n"
            f"After losses: {post_R}R per trade\n"
            f"Behavioral shift: {delta_R}R per trade\n"
            f"Estimated impact over period: ₹{impact_rupees}"
        )