from enum import Enum, auto


class DeliveryStrategy(Enum):
    INLINE_COMPREHENSIVE = auto()
    ON_DEMAND_LINK = auto()
    INDEXED_CHUNKS = auto()


class TokenEstimator:
    """
    Estimates token counts using a fast heuristic and recommends context strategies.
    """

    def __init__(self, chars_per_token: float = 4.0):
        self.chars_per_token = chars_per_token

    def estimate_tokens(self, text: str) -> int:
        """
        Estimates the number of tokens in the given text.
        """
        return int(len(text) / self.chars_per_token)

    def recommend_strategy(self, tokens: int, budget: int) -> DeliveryStrategy:
        """
        Recommends a delivery strategy based on estimated tokens vs budget.
        """
        if tokens > budget:
            return DeliveryStrategy.ON_DEMAND_LINK
        return DeliveryStrategy.INLINE_COMPREHENSIVE
