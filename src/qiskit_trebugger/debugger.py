from qiskit import QuantumCircuit, transpile, __qiskit_version__
from qiskit.providers import BaseBackend
from qiskit.providers.backend import Backend
from qiskit.transpiler.basepasses import AnalysisPass, TransformationPass

from typing import Optional, Union
import logging
import warnings

from IPython.display import display

from qiskit_trebugger.model import TranspilerLoggingHandler
from qiskit_trebugger.model import TranspilerDataCollector
from qiskit_trebugger.model import TranspilationSequence
from qiskit_trebugger.views.widget.timeline_view import TimelineView
from .debugger_error import DebuggerError


class Debugger:
    @classmethod
    def debug(
        cls,
        circuit: QuantumCircuit,
        backend: Optional[Union[Backend, BaseBackend]] = None,
        optimization_level: Optional[int] = None,
        **kwargs
    ):

        if not isinstance(circuit, QuantumCircuit):
            raise DebuggerError(
                "Debugger currently supports single QuantumCircuit only!"
            )

        # Create the view:
        view = TimelineView()

        def on_step_callback(step):
            view.add_step(step)

        # Prepare the model:
        transpilation_sequence = TranspilationSequence(on_step_callback)

        warnings.simplefilter("ignore")
        transpilation_sequence.general_info = {
            "Backend": backend.name(),
            "optimization_level": optimization_level,
            "Qiskit version": __qiskit_version__["qiskit"],
            "Terra version": __qiskit_version__["qiskit-terra"],
        }

        transpilation_sequence.original_circuit = circuit

        warnings.simplefilter("default")

        Debugger._register_logging_handler(transpilation_sequence)
        transpiler_callback = Debugger._get_data_collector(transpilation_sequence)

        # Pass the model to the view:
        view.transpilation_sequence = transpilation_sequence
        view.update_params(**kwargs)

        display(view)

        transpile(
            circuit,
            backend,
            optimization_level=optimization_level,
            callback=transpiler_callback,
            **kwargs
        )

        view.update_summary()
        view.add_class("done")

    @classmethod
    def _register_logging_handler(cls, transpilation_sequence):

        # TODO: Do not depend on loggerDict
        all_loggers = logging.Logger.manager.loggerDict
        passes_loggers = {
            key: value
            for (key, value) in all_loggers.items()
            if key.startswith("qiskit.transpiler.passes.")
        }

        loggers_map = {}
        for _pass in AnalysisPass.__subclasses__():
            if _pass.__module__ in passes_loggers.keys():
                loggers_map[_pass.__module__] = _pass.__name__

        for _pass in TransformationPass.__subclasses__():
            if _pass.__module__ in passes_loggers.keys():
                loggers_map[_pass.__module__] = _pass.__name__

        handler = TranspilerLoggingHandler(
            transpilation_sequence=transpilation_sequence, loggers_map=loggers_map
        )
        logger = logging.getLogger("qiskit.transpiler.passes")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    @classmethod
    def _get_data_collector(cls, transpilation_sequence):
        return TranspilerDataCollector(transpilation_sequence).transpiler_callback
