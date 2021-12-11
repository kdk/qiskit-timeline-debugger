from collections import defaultdict


class Property:
    LARGE_VALUE_THRESHOLD = 2000

    def __init__(self, name, type, value, state) -> None:
        self.name = name
        self.type = type
        self.state = state

        if (type == list or type == defaultdict) and (
            len(value) > self.LARGE_VALUE_THRESHOLD
        ):
            print(len(value))
            self.value = "LARGE_VALUE"
        else:
            self.value = value

    def __repr__(self) -> str:
        return f"{self.name} ({self.type.__name__}) : {self.value}"
