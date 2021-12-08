from collections import defaultdict
from .pass_type import PassType
from .property import Property
from .transpilation_step import TranspilationStep


class TranspilerDataCollector:
    def __init__(self, transpilation_sequence) -> None:
        self.transpilation_sequence = transpilation_sequence
        self._properties = {}

        def callback(**kwargs):
            pass_ = kwargs["pass_"]

            pass_name = pass_.name()
            pass_type = ""
            if pass_.is_analysis_pass:
                pass_type = PassType.ANALYSIS
            elif pass_.is_transformation_pass:
                pass_type = PassType.TRANSFORMATION

            transpilation_step = TranspilationStep(pass_name, pass_type)
            transpilation_step.docs = pass_.__doc__
            transpilation_step.run_method_docs = getattr(pass_, "run").__doc__

            duration_value = round(1000 * kwargs["time"], 2)
            transpilation_step.duration = duration_value

            # Properties
            property_set = kwargs["property_set"]
            _added_props = []
            _updated_props = []
            for key in property_set:
                value = property_set[key]
                if key not in self._properties.keys():
                    _added_props.append(key)
                elif (self._properties[key] is None) and (value is not None):
                    _updated_props.append(key)
                elif hasattr(value, "__len__") and (
                    len(value) != len(self._properties[key])
                ):
                    _updated_props.append(key)

            if len(_added_props) > 0 or len(_updated_props) > 0:
                for property_name in property_set:
                    self._properties[property_name] = property_set[property_name]

                    property_type = type(property_set[property_name])
                    property_value = property_set[property_name]

                    property_state = ""
                    if property_name in _added_props:
                        property_state = "new"
                    elif property_name in _updated_props:
                        property_state = "updated"

                    transpilation_step.property_set[property_name] = Property(
                        property_name, property_type, property_value, property_state
                    )

            from copy import deepcopy

            dag = deepcopy(kwargs["dag"])

            # circuit stats:
            if pass_.is_analysis_pass and len(self.transpilation_sequence.steps) > 0:
                transpilation_step.circuit_stats = self.transpilation_sequence.steps[
                    -1
                ].circuit_stats
            else:
                transpilation_step.circuit_stats.width = dag.width()
                transpilation_step.circuit_stats.size = dag.size()
                transpilation_step.circuit_stats.depth = dag.depth()

                nodes = dag.op_nodes(include_directives=False)
                circ_ops_1q = 0
                circ_ops_2q = 0
                circ_ops_3q = 0
                for node in nodes:
                    operands_count = len(node.qargs)
                    if operands_count == 1:
                        circ_ops_1q += 1
                    elif operands_count == 2:
                        circ_ops_2q += 1
                    else:
                        circ_ops_3q += 1

                transpilation_step.circuit_stats.ops_1q = circ_ops_1q
                transpilation_step.circuit_stats.ops_2q = circ_ops_2q
                transpilation_step.circuit_stats.ops_3q = circ_ops_3q

            # Store `dag` to use it for circuit plot generation:
            if (
                transpilation_step.type == PassType.TRANSFORMATION
                and transpilation_step.circuit_stats.depth <= 300
            ):
                transpilation_step.dag = dag

            self.transpilation_sequence.add_step(transpilation_step)

        self._transpiler_callback = callback

    @property
    def transpiler_callback(self):
        return self._transpiler_callback
