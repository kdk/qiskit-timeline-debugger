class CircuitStats:
    def __init__(self) -> None:
        self.width = None
        self.size = None
        self.depth = None
        self.ops_1q = None
        self.ops_2q = None
        self.ops_3q = None

    def __eq__(self, other):
        return self.width == other.width and self.size == other.size and self.depth == other.depth and self.ops_1q == other.ops_1q and self.ops_2q == other.ops_2q and self.ops_3q == other.ops_3q

    def __repr__(self) -> str:
        return f"CircuitStats(width={self.width}, size={self.size}, depth={self.depth}, 1q-ops={self.ops_1q}, 2q-ops={self.ops_2q}, 3+q-ops={self.ops_3q})"