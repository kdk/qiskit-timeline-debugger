from time import time

class LogEntry:
    def __init__(self, levelname, msg, args) -> None:
        self.levelname = levelname
        self.msg = msg
        self.args = args
        self.time = time()

    def __repr__(self) -> str:
        return f"[{self.levelname}] {self.msg}"