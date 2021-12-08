from qiskit import QuantumCircuit
from qiskit.converters import dag_to_circuit, circuit_to_dag
from numpy import zeros, uint16

# make the global DP array
LCS_DP = zeros((2000, 2000), dtype=uint16)


class CircuitComparator:
    @staticmethod
    def get_moments(dag):
        moments = [l["graph"] for l in list(dag.layers())]
        return moments

    @staticmethod
    def make_LCS(moments1, moments2) -> None:
        # moments1 : list of lists
        # m2 : list of lists

        # clear for the base cases of dp
        for i in range(2000):
            LCS_DP[i][0], LCS_DP[0][i] = 0, 0

        n, m = len(moments1), len(moments2)

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                # if the layers are isomorphic then okay
                if moments1[i - 1] == moments2[j - 1]:
                    LCS_DP[i][j] = 1 + LCS_DP[i - 1][j - 1]
                else:
                    LCS_DP[i][j] = max(LCS_DP[i - 1][j], LCS_DP[i][j - 1])

    @staticmethod
    def compare(prev_circ, curr_circ) -> QuantumCircuit:
        if prev_circ is None:
            return (False, curr_circ)

        # update by reference as there is no qasm now
        prev_dag = circuit_to_dag(prev_circ)
        curr_dag = circuit_to_dag(curr_circ)

        moments1 = CircuitComparator.get_moments(prev_dag)
        moments2 = CircuitComparator.get_moments(curr_dag)

        CircuitComparator.make_LCS(moments1, moments2)

        (n, m) = (len(moments1), len(moments2))

        id_set = set()
        i = n
        j = m

        while i > 0 and j > 0:
            if moments1[i - 1] == moments2[j - 1]:

                # just want diff for second one
                id_set.add(j - 1)
                i -= 1
                j -= 1

            else:
                if LCS_DP[i - 1][j] > LCS_DP[i][j - 1]:
                    # means the graph came from the
                    # first circuit , go up
                    i -= 1
                else:
                    # if equal or small, go left
                    j -= 1

        # if the whole circuit has not changed

        fully_changed = len(id_set) == 0

        if not fully_changed:
            for id2, l in enumerate(list(curr_dag.layers())):
                if id2 not in id_set:
                    # this is not an LCS node -> highlight it
                    for node in l["graph"].front_layer():
                        node.name = node.name + " "

        return (fully_changed, dag_to_circuit(curr_dag))
