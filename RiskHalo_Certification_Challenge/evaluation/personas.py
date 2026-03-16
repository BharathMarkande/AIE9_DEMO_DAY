# Dictionary of structured trader archetypes used for
# persona-driven RAG evaluation and robustness testing.
"""
Defines structured trader personas used for evaluation and stress-testing
the RiskHalo RAG system. Each persona is defined by:
- A description of the trader's behavior
- A list of question templates that can be used to evaluate the RAG system
"""

TRADER_PERSONAS = {
    "revenge_trader": {
        "description": (
            "Trader prone to emotional escalation after losses. "
            "Often increases risk, overtrades, and breaches daily limits."
        ),
        "behavioral_state": "LOSS_ESCALATION",
        "question_templates": [
            "Why do my losses increase after a losing trade?",
            "Am I escalating risk after losses?",
            "What does my post-loss performance indicate?",
            "Is my behavior unstable after red days?"
        ],
    },
    "premature_profit_taker": {
        "description": (
            "Trader with high win rate but low average R. "
            "Exits profitable trades too early."
        ),
        "behavioral_state": "CONFIDENCE_CONTRACTION",
        "question_templates": [
            "Why is my expectancy negative despite winning often?",
            "Am I cutting profits too early?",
            "How is my R:R affecting long-term results?",
            "Are my winners too small?"
        ],
    },
    "disciplined_but_unprofitable": {
        "description": (
            "Trader who follows risk rules but struggles with profitability."
        ),
        "behavioral_state": "STABLE",
        "question_templates": [
            "I follow rules but still lose. Why?",
            "Is discipline enough to be profitable?",
            "Is my strategy flawed?",
            "What is structurally wrong in my performance?"
        ],
    },
    "adaptive_trader": {
        "description": (
            "Trader who improves after losses and maintains discipline."
        ),
        "behavioral_state": "ADAPTIVE_RECOVERY",
        "question_templates": [
            "Am I improving over time?",
            "Is my recovery behavior healthy?",
            "What strengths should I reinforce?",
            "Is my execution becoming more stable?"
        ],
    },
    "low_data_trader": {
        "description": (
            "Trader with very few trades and limited post-loss activity."
        ),
        "behavioral_state": "INSUFFICIENT_POST_LOSS_DATA",
        "question_templates": [
            "Is there enough data to evaluate my behavior?",
            "What can be inferred from a small sample?",
            "How reliable is this week's analysis?",
            "What should I track more closely?"
        ],
    },
}


# Use when testing locally to avoid API costs
# TRADER_PERSONAS = {
#     "revenge_trader": {
#         "description": (
#             "Trader prone to emotional escalation after losses. "
#             "Often increases risk, overtrades, and breaches daily limits."
#         ),
#         "behavioral_state": "LOSS_ESCALATION",
#         "question_templates": [
#             "Why do my losses increase after a losing trade?",
#             "Am I escalating risk after losses?",
#             "What does my post-loss performance indicate?",
#             "Is my behavior unstable after red days?"
#         ],
#     }
# }