import logging
from .log_entry import LogEntry

class TranspilerLoggingHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.loggers_map = kwargs['loggers_map']
        kwargs.pop('loggers_map', None)

        self.transpilation_sequence = kwargs['transpilation_sequence']
        kwargs.pop('transpilation_sequence', None)

        super(TranspilerLoggingHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        log_entry = LogEntry(record.levelname, record.msg, record.args)
        self.transpilation_sequence.add_log_entry(self.loggers_map[record.name], log_entry)