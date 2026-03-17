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
            "There were too few trades taken immediately after a loss to compare your behavior reliably.\n"
            "To measure how you behave after losses, the model needs enough post-loss trades to form a group.\n"
            "For this period, no economic impact from post-loss behavior is estimated."
        )

    # --------------------------------------------------
    # STABLE
    # --------------------------------------------------
    if behavioral_state == "STABLE":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"On average, your trades were fairly consistent at around ₹{normal_rupees} per trade.\n"
                "Your behavior after losses did not meaningfully change your results versus normal conditions.\n"
                "For this period, there is no clear evidence that post-loss trading is hurting your performance."
            )
        else:
            return (
                "Performance Impact\n"
                f"On average, your trades were fairly consistent at about {normal_R}R per trade.\n"
                "Your behavior after losses did not meaningfully change your results versus normal conditions.\n"
                "For this period, there is no clear evidence that post-loss trading is hurting your performance."
            )

    # --------------------------------------------------
    # LOSS_ESCALATION
    # --------------------------------------------------
    if behavioral_state == "LOSS_ESCALATION":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"On trades taken right after a loss, you lost about ₹{abs(post_rupees)} per trade on average.\n"
                f"Over this period, continuing to trade after losses cost you about ₹{abs(impact_rupees)} in additional losses compared with stopping after a loss.\n"
                "This pattern is typical of revenge trading after losses, where you keep trading in a degraded state and give back more than your planned risk."
            )
        else:
            return (
                "Performance Impact\n"
                f"Normal trades averaged {normal_R}R per trade.\n"
                f"After losses, trades averaged {post_R}R per trade.\n"
                f"Over this period, that deterioration reduced performance by about ₹{abs(impact_rupees)} compared with stopping after a loss."
            )

    # --------------------------------------------------
    # CONFIDENCE_CONTRACTION
    # --------------------------------------------------
    if behavioral_state == "CONFIDENCE_CONTRACTION":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"In normal conditions, your trades averaged about ₹{normal_rupees} per trade.\n"
                f"After losses, your average result slipped to about ₹{post_rupees} per trade, mainly because you took profits earlier and let winners run less.\n"
                "This points to profit compression after drawdowns — you become more cautious and cut winners sooner, rather than taking larger losses.\n"
                f"Over this period, that behavior change reduced your results by roughly ₹{abs(impact_rupees)} compared with keeping the same profit targets after losses."
            )
        else:
            return (
                "Performance Impact\n"
                f"In normal conditions, your trades averaged about {normal_R}R per trade.\n"
                f"After losses, this dropped to about {post_R}R per trade, mostly due to smaller wins rather than bigger losses.\n"
                "This points to profit compression after drawdowns — more cautious exits and earlier profit-taking.\n"
                f"Over this period, that behavior change reduced your results by roughly ₹{abs(impact_rupees)} compared with keeping the same profit targets after losses."
            )

    # --------------------------------------------------
    # ADAPTIVE_RECOVERY
    # --------------------------------------------------
    if behavioral_state == "ADAPTIVE_RECOVERY":
        if risk_per_trade:
            return (
                "Performance Impact\n"
                f"In normal conditions, your trades averaged about ₹{normal_rupees} per trade.\n"
                f"After losses, your average result actually improved to around ₹{post_rupees} per trade.\n"
                "This suggests you respond to losses constructively — you tighten up and execute better instead of chasing or freezing.\n"
                f"Over this period, that adaptive response added roughly ₹{abs(impact_rupees)} to your results compared with stopping at the normal level."
            )
        else:
            return (
                "Performance Impact\n"
                f"In normal conditions, your trades averaged about {normal_R}R per trade.\n"
                f"After losses, this improved to about {post_R}R per trade.\n"
                "This suggests an adaptive recovery pattern — your execution quality improves following setbacks.\n"
                f"Over this period, that adaptive response added roughly ₹{abs(impact_rupees)} to your results compared with staying at the normal level."
            )
            
            
    return (
        "Performance Impact\n"
        f"In normal conditions, trades averaged about {normal_R}R per trade.\n"
        f"After losses, trades averaged about {post_R}R per trade.\n"
        f"The difference between these two modes corresponds to roughly ₹{impact_rupees} in impact over this period.\n"
        "This captures how much your performance changes when you are trading after losses versus in neutral conditions."
    )