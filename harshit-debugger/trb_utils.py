from gzip import GzipFile
from ipywidgets import Output, HBox, Layout, HTML
from IPython.display import display
from numpy import exp, uint16
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from layouts import Layouts, Download_Button, Styles, Headings
from types import ModuleType, FunctionType
from gc import get_referents
from sys import getsizeof
from numpy import zeros

LCS_DP = zeros((4000, 4000), dtype=uint16)


BLACKLIST = type, ModuleType, FunctionType

LCS_DP = zeros((4000, 4000), dtype=uint16)


BLACKLIST = type, ModuleType, FunctionType


def get_scale(x):
    # a simple decreasing function with a gentle slope
    return (1 / (1 + exp(0.06 * x))) + 0.6


def get_size(obj):
    """sum size of object & members."""
    # if isinstance(obj, BLACKLIST):
    #    raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                # if id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size


def write_string(data, fname):
    f = GzipFile(fname, "wb")
    f.write(data)


def write_depth(depth):
    file = open("debug-info/depth.txt", "a")
    file.write(depth)


def get_circuit(fname):
    f = GzipFile(fname, "rb")
    qasm = f.read().decode()
    return QuantumCircuit.from_qasm_str(qasm)


def get_depth(count):
    f = open("debug-info/depth.txt", "r")
    for row in f.readlines():
        idx, depth = row.split("-")
        if idx == count:
            return int(depth)


def get_moments(dag):
    moments = [l["graph"] for l in list(dag.layers())]
    return moments


def make_LCS(m1, m2):
    # m1 : list of lists
    # m2 : list of lists

    # clear for the base cases of dp
    for i in range(4000):
        LCS_DP[i][0], LCS_DP[0][i] = 0, 0

    n, m = len(m1), len(m2)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # if the layers are isomorphic then okay
            if m1[i - 1] == m2[j - 1]:
                LCS_DP[i][j] = 1 + LCS_DP[i - 1][j - 1]
            else:
                LCS_DP[i][j] = max(LCS_DP[i - 1][j], LCS_DP[i][j - 1])


def make_diff(q1, q2):

    if q1 is None:
        return q2

    d1, d2 = circuit_to_dag(q1), circuit_to_dag(q2)

    m1 = get_moments(d1)
    m2 = get_moments(d2)

    make_LCS(m1, m2)

    # start from bottom
    n, m = len(m1), len(m2)

    id_set = set([j for j in range(m)])
    i, j = n, m

    while i > 0 and j > 0:
        if m1[i - 1] == m2[j - 1]:
            # just want diff for second one
            id_set.remove(j - 1)
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

    # change q2 by reference
    for id2, l in enumerate(list(d2.layers())):
        if id2 in id_set:
            # this is a non LCS node
            for node in l["graph"].front_layer():
                node.name = node.name + " "

    result = dag_to_circuit(d2)

    return result


def add_image(change):
    parent = change["owner"]

    # generate the path of the current circuit and
    # immediately previous circuit

    count = (parent.get_title(0)).split("-")[1]

    # generate paths ( index based now )
    path_curr = "debug-info/qasm/" + count + ".gz"

    # get the previous circuit path
    if int(count) != 0:
        path_prev = "debug-info/qasm/" + str(int(count) - 1) + ".gz"
    else:
        path_prev = None

    children = list(parent.children[0].children)

    # selected index is zero right now means accordion is selected
    if change["new"] == 0:

        if children[0].children[0] == Headings.transform_label:
            type_pass = "T"
        else:
            type_pass = "A"

        # accordion has been selected, build the output widget

        out = Output(layout=Layouts.output_layout)

        depth = get_depth(count)

        # in any case diff is calculated so that
        # user can atleast download the image

        if type_pass == "T":
            # only transformations change circuit
            curr_circ = get_circuit(path_curr)
            prev_circ = None if path_prev is None else get_circuit(path_prev)

            # here, the current circuit's gate names are updated
            diff_circ = make_diff(prev_circ, curr_circ)

        else:
            diff_circ = get_circuit(path_curr)

        if depth > 90:
            with out:
                display(
                    HTML(
                        f'<h2 style="margin :10% 3% 10% 3%; font-weight:bold;"> Circuit Depth {depth} too large to be displayed </h2>'
                    )
                )

        else:

            # get scale
            area = diff_circ.size()

            # scale accordingly
            out.append_display_data(
                HTML(f"<h2 style='margin-left:30px'><b>Circuit State</b></h2>")
            )
            with out:
                display(
                    diff_circ.draw(
                        "mpl", scale=get_scale(area), style=Styles.diff_style
                    )
                )

        # provide a download utility to the user for
        # the diff circuit

        download_image = Download_Button(
            name=parent.get_title(0),
            circuit=diff_circ,
            button_type="circ_img",
            description="Download Image",
            icon="cloud-download",
        )

        download_qpy = Download_Button(
            name=parent.get_title(0),
            circuit=diff_circ,
            button_type="circ_qpy",
            description="Download .qpy",
            icon="cloud-download",
        )

        download_box = HBox([download_image, download_qpy])

        with out:
            display(download_box)

        # now update the children of the accordion
        children = [out] + children

    else:
        # need to cater to first time display also
        if len(children) == 1:
            pass
        else:
            children[0].clear_output()
            del children[0]
        # remove the output widget

    change["owner"].children = [HBox(children, layout=Layout(display="center"))]

