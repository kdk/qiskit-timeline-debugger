from .circuit_stats import CircuitStats


class TranspilationStep:
    def __init__(self, name, type) -> None:
        self.index = None
        self.name = name
        self.type = type
        self.docs = ""
        self.run_method_docs = ""
        self.duration = 0
        self.circuit_stats = CircuitStats()
        self.property_set = {}
        self.property_set_index = None
        self.logs = []
        self.dag = None

    def __repr__(self) -> str:
        return f"(name={self.name}, type={self.type})"
