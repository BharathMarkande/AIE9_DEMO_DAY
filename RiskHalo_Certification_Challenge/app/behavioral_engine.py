import numpy as np


class BehavioralEngine:
    """
    BehavioralEngine diagnoses emotional execution distortion by comparing
    performance in neutral trades versus trades placed immediately after losses.

    It detects:
    - Expectancy deterioration
    - Win-size contraction
    - Loss-size expansion

    The engine supports confidence tiers to ensure statistical integrity:
        - HIGH: Sufficient data in both groups (>= 2 trades each)
        - LOW: Limited sample size
        - NO_POST_LOSS_DATA: No post-loss trades present

    The engine always returns structured output and never fails ingestion.
    """

    def __init__(self, df):
        self.df = df.copy()

        if "post_loss_flag" not in self.df.columns:
            raise ValueError("FeatureEngine must be run before BehavioralEngine.")

        self.analysis_confidence = "HIGH"

    # --------------------------------------------------
    # Split Groups
    # --------------------------------------------------
    def split_groups(self):
        """
        Segments trades into behavioral contexts:

        - Normal trades (post_loss_flag == 0)
        - Post-loss trades (post_loss_flag == 1)

        Determines statistical confidence tier:

        HIGH:
            Both groups contain >= 2 trades.

        LOW:
            One group contains fewer than 2 trades.

        NO_POST_LOSS_DATA:
            No post-loss trades exist, making distortion comparison impossible.

        This method never raises exceptions and prepares the engine
        for safe downstream metric computation.
        """

        self.normal_df = self.df[self.df["post_loss_flag"] == 0]
        self.post_df = self.df[self.df["post_loss_flag"] == 1]

        normal_count = len(self.normal_df)
        post_count = len(self.post_df)

        #No post-loss data
        if post_count == 0:
            self.analysis_confidence = "NO_POST_LOSS_DATA"

        #Limited data
        elif normal_count < 2 or post_count < 2:
            self.analysis_confidence = "LOW"

        #Otherwise HIGH
        else:
            self.analysis_confidence = "HIGH"

    # --------------------------------------------------
    # Compute Group Metrics
    # --------------------------------------------------
    def compute_metrics(self):
        """
        Computes core performance statistics separately for
        normal and post-loss trade groups.

        Metrics calculated:
        - Average R (risk-normalized expectancy)
        - Average winning R
        - Average losing R
        - Win rate

        Handles empty groups safely by returning zeros.

        These metrics form the quantitative basis
        for behavioral distortion analysis.
        """

        def group_stats(group):

            if len(group) == 0:
                return 0, 0, 0, 0

            avg_R = group["R_proxy"].mean()

            wins = group[group["R_proxy"] > 0]
            losses = group[group["R_proxy"] < 0]

            avg_win_R = wins["R_proxy"].mean() if len(wins) > 0 else 0
            avg_loss_R = losses["R_proxy"].mean() if len(losses) > 0 else 0

            win_rate = len(wins) / len(group) if len(group) > 0 else 0

            return avg_R, avg_win_R, avg_loss_R, win_rate

        (
            self.avg_R_normal,
            self.avg_win_R_normal,
            self.avg_loss_R_normal,
            self.win_rate_normal,
        ) = group_stats(self.normal_df)

        (
            self.avg_R_post,
            self.avg_win_R_post,
            self.avg_loss_R_post,
            self.win_rate_post,
        ) = group_stats(self.post_df)

    # --------------------------------------------------
    # Compute Distortions
    # --------------------------------------------------
    def compute_distortions(self):
        """
        Quantifies behavioral distortion magnitude by measuring
        percentage change between normal and post-loss metrics.

        Distortion Components:
        - R_drop_percent:
            Overall expectancy deterioration.
        - win_shrink_percent:
            Reduction in average winning size.
        - loss_expansion_percent:
            Increase in average loss size.

        Safely handles division-by-zero cases.

        These metrics express emotional distortion intensity.
        """

        self.R_drop_percent = (
            (self.avg_R_normal - self.avg_R_post) / abs(self.avg_R_normal)
            if self.avg_R_normal != 0 else 0
        )

        self.win_shrink_percent = (
            (self.avg_win_R_normal - self.avg_win_R_post) / abs(self.avg_win_R_normal)
            if self.avg_win_R_normal != 0 else 0
        )

        self.loss_expansion_percent = (
            (abs(self.avg_loss_R_post) - abs(self.avg_loss_R_normal)) / abs(self.avg_loss_R_normal)
            if self.avg_loss_R_normal != 0 else 0
        )

    # --------------------------------------------------
    # Classify Behavioral State
    # --------------------------------------------------
    def classify_behavior(self):
        """
        Classifies the trader's behavioral state using
        deterministic thresholds.

        Possible states:
        - STABLE:
            No meaningful distortion detected.
        - CONFIDENCE_CONTRACTION:
            Win size shrinks after losses.
        - LOSS_ESCALATION:
            Loss size expands after losses.
        - ADAPTIVE_RECOVERY:
            Performance improves post-loss.
        - INSUFFICIENT_POST_LOSS_DATA:
            No comparison possible.

        Converts statistical shifts into psychologically
        interpretable execution states.
        """

        threshold = 0.25

        # If no post-loss data, no distortion comparison possible
        if self.analysis_confidence == "NO_POST_LOSS_DATA":
            self.behavioral_state = "INSUFFICIENT_POST_LOSS_DATA"
            return

        if self.avg_R_post > self.avg_R_normal:
            self.behavioral_state = "ADAPTIVE_RECOVERY"

        elif self.loss_expansion_percent > threshold:
            self.behavioral_state = "LOSS_ESCALATION"

        elif self.win_shrink_percent > threshold:
            self.behavioral_state = "CONFIDENCE_CONTRACTION"

        else:
            self.behavioral_state = "STABLE"

    # --------------------------------------------------
    # Compute Severity
    # --------------------------------------------------
    def compute_severity(self):
        """
        Computes normalized severity score (0–1) representing
        emotional distortion magnitude.

        Severity is calculated as the mean of positive
        distortion components:
        - R_drop_percent
        - win_shrink_percent
        - loss_expansion_percent

        Improvements are ignored (only deterioration counted).

        LOW confidence reduces severity by 50%
        to avoid overfitting small samples.

        NO_POST_LOSS_DATA results in zero severity.
        """

        if self.analysis_confidence == "NO_POST_LOSS_DATA":
            self.severity_score = 0
            return

        components = [
            max(0, self.R_drop_percent),
            max(0, self.win_shrink_percent),
            max(0, self.loss_expansion_percent),
        ]

        severity = min(1, np.mean(components))

        # Damp severity if LOW confidence
        if self.analysis_confidence == "LOW":
            severity *= 0.5

        self.severity_score = severity

    # --------------------------------------------------
    # Run Full Diagnosis
    # --------------------------------------------------
    def run(self):
        """
        Executes full behavioral diagnosis pipeline:

        1. Segment trades by emotional context
        2. Compute group performance metrics
        3. Quantify distortion percentages
        4. Classify behavioral state
        5. Compute confidence-adjusted severity

        Returns
        -------
        dict
            Structured behavioral diagnosis including:
            - behavioral_state
            - severity_score
            - analysis_confidence
            - group-level metrics
            - distortion percentages

        This output feeds the ExpectancyEngine,
        RuleComplianceEngine, and downstream coaching agents.
        """

        self.split_groups()
        self.compute_metrics()
        self.compute_distortions()
        self.classify_behavior()
        self.compute_severity()

        return {
            "behavioral_state": self.behavioral_state,
            "severity_score": round(self.severity_score, 3),
            "analysis_confidence": self.analysis_confidence,

            "avg_R_normal": round(self.avg_R_normal, 3),
            "avg_R_post": round(self.avg_R_post, 3),

            "avg_win_R_normal": round(self.avg_win_R_normal, 3),
            "avg_win_R_post": round(self.avg_win_R_post, 3),

            "avg_loss_R_normal": round(self.avg_loss_R_normal, 3),
            "avg_loss_R_post": round(self.avg_loss_R_post, 3),

            "win_rate_normal": round(self.win_rate_normal, 3),
            "win_rate_post": round(self.win_rate_post, 3),

            "R_drop_percent": round(self.R_drop_percent, 3),
            "win_shrink_percent": round(self.win_shrink_percent, 3),
            "loss_expansion_percent": round(self.loss_expansion_percent, 3),
        }