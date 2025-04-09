import time

class TokenBucket:
    def __init__(self, initial_tokens: int, max_tokens: int, refill_interval: float):
        self.max_tokens = max_tokens
        self.refill_interval = refill_interval
        self.tokens = initial_tokens
        self.last_refill_time = time.time()

    def _refill_tokens(self):
        now = time.time()
        elapsed = now - self.last_refill_time
        refill_tokens = int(elapsed / self.refill_interval)
        
        if refill_tokens > 0:
            self.tokens = min(self.max_tokens, self.tokens + refill_tokens)
            self.last_refill_time += refill_tokens * self.refill_interval

    def consume(self, tokens: int = 1) -> bool:
        self._refill_tokens()

        # If we have enough tokens to subtract
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False