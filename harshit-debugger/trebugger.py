from ipywidgets import Accordion, Output, Box, Button, HBox, VBox, Button, HTML
from qiskit import transpile
import ipywidgets as widgets
from qiskit.converters import dag_to_circuit
from shutil import rmtree
from IPython.display import display
from os import makedirs
from qiskit.version import __qiskit_version__
from layouts import *
from trb_utils import *
from base64 import b64encode

# debugger view
main_view = Output()


class Overview:
    total_passes = dict(A=0, T=0)
    depths = dict(init=0, final=0)
    op_count = dict(init=0, final=0)

    @classmethod
    def clear(cls):
        cls.total_passes["A"] = cls.total_passes["T"] = 0
        cls.depths["init"] = cls.depths["final"] = 0
        cls.op_count["init"] = cls.op_count["final"] = 0


class PreviousPass:

    # make property class to take note of the previous properties
    property_map = dict()
    property_acc = Accordion()  # to store previous properties

    # make the circuit stats map to take note of current properties
    circuit_props = dict()
    circuit_prop_acc = Accordion()  # to store previous circuit stats

    @classmethod
    def clear(cls):
        cls.property_map.clear()
        cls.property_acc.children = []
        cls.circuit_props.clear()
        cls.circuit_prop_acc.children = []


def advanced_callback(dag, pass_, time, property_set, count):

    # write the image to qasm string

    # 1. Save the circuit in qasm
    qasm_string = dag_to_circuit(dag).qasm().encode()
    depth_entry = str(count) + "-" + str(dag.depth())

    # 2. make file name

    fname = str(count) + ".gz"
    path = "debug-info/qasm/" + fname

    # 3. save in the file
    write_string(qasm_string, path)
    write_depth(depth_entry + "\n")

    pass_type = None

    if pass_.is_analysis_pass:
        pass_type = "A"
        Overview.total_passes["A"] += 1
    else:
        pass_type = "T"
        Overview.total_passes["T"] += 1

    # make a box of properties
    if pass_type == "A":
        head = Headings.analyse_label
    else:
        head = Headings.transform_label

    time_taken = Button(
        description="Time : " + str(round(time, 5)) + "ms",
        style=Styles.button_style2,
        disabled=True,
        layout=dict(width="auto", height="35px", display="center", margin="0 3% 0 3%"),
    )

    # 2. encapsulate property map in accordion

    # this needs to be done only if analysis pass
    acc1 = Accordion(layout=Layouts.acc_layout)
    acc1.set_title(0, "Property Set")
    acc1.selected_index = None

    if pass_type == "A" or len(PreviousPass.property_acc.children) == 0:
        props = []
        for prop, value in property_set.items():
            if prop != "layout":

                style = "primary"

                if pass_type == "A" or len(PreviousPass.property_map.keys()) == 0:
                    if prop not in PreviousPass.property_map:
                        style = "success"
                    else:
                        # if in but value changed then orange
                        # note : don't account for big value property
                        if (
                            PreviousPass.property_map[prop] != True
                            and PreviousPass.property_map[prop] != value
                        ):
                            style = "warning"

                if get_size(value) < 2 ** 16:
                    props.append(
                        Button(
                            description=str(prop) + "  :  " + str(value),
                            layout=Layouts.items_layout,
                            button_style=style,
                        )
                    )
                    PreviousPass.property_map[prop] = value
                else:
                    props.append(
                        Button(
                            description=str(prop) + "  :  " + "...",
                            layout=Layouts.items_layout,
                            button_style=style,
                        )
                    )
                    # not keeping very big property sets and thus not checking their changes
                    PreviousPass.property_map[prop] = True

        box1 = Box(children=props, layout=Layouts.box_layout2,)

        acc1.children = [box1]

        # update the property acc
        PreviousPass.property_acc.children = acc1.children
    else:
        if len(PreviousPass.property_acc.children) != 0:
            acc1.children = PreviousPass.property_acc.children

    # 3. encapsulate circuit properties in accordion
    acc2 = Accordion(layout=Layouts.acc_layout)
    acc2.set_title(0, "Circuit Properties")
    acc2.selected_index = None

    # update the overview panel
    Overview.depths["final"] = dag.depth()
    Overview.op_count["final"] = len(dag.op_nodes(include_directives=False))

    if pass_type == "T" or len(PreviousPass.circuit_prop_acc.children) == 0:
        props = []

        one_q_ops, two_q_ops = 0, 0

        nodes = dag.op_nodes(include_directives=False)

        for node in nodes:
            if len(node.qargs) > 1:
                two_q_ops += 1
            else:
                one_q_ops += 1

        dag_properties = {
            "Width": dag.width(),
            "Size": dag.size(),
            "1-Q ops": one_q_ops,
            "2-Q ops": two_q_ops,
        }

        for prop, value in dag_properties.items():
            style = "primary"
            if pass_type == "T" or len(PreviousPass.circuit_props.keys()) == 0:
                if prop not in PreviousPass.circuit_props:
                    style = "success"
                else:
                    if PreviousPass.circuit_props[prop] != value:
                        style = "warning"

            props.append(
                Button(
                    description=str(prop) + "  :  " + str(value),
                    layout=Layouts.items_layout,
                    button_style=style,
                )
            )
            PreviousPass.circuit_props[prop] = value

        box2 = Box(children=props, layout=Layouts.box_layout2,)

        acc2.children = [box2]
        # update circuit stats
        PreviousPass.circuit_prop_acc.children = acc2.children  # update children

    else:
        if len(PreviousPass.circuit_prop_acc.children) != 0:
            acc2.children = PreviousPass.circuit_prop_acc.children

    # 4. get the logs here
    # log_acc = Accordion(layout=Layouts.acc_layout)
    # log_acc.set_title(0, "Logs")
    # log_out = Output()

    # """TO DO"""

    #     with log_out:
    #         get_correct_log(count)
    # now associate this log with the correct pass in the transpiler

    # log_acc.children = [log_out]
    # log_acc.selected_index = None  # polymorphism used here!!

    description = VBox([head, time_taken, acc1, acc2], layout=Layouts.box_layout)

    # make a new accordion
    new_child = HBox([description], layout=dict(display="center"))

    # this new accordion's children are manipulated
    # how? the output widget is added as the first child of the accordion's
    # HBox and when collapsed, it is removed so that the image
    # is not loaded there.

    new_acc = Accordion()
    new_acc.children = [new_child]
    new_acc.set_title(0, pass_.name() + "-" + str(count))
    new_acc.selected_index = None
    new_acc.observe(add_image, names=["selected_index"])

    with main_view:
        display(new_acc)


def basic_callback(dag, pass_, time, property_set, count):

    # write the image to qasm string

    # 1. No display is required, no visual approach
    qasm_string = dag_to_circuit(dag).qasm().encode()
    depth_entry = str(count) + "-" + str(dag.depth())

    # 2. make file name
    fname = str(count) + ".gz"
    path = "debug-info/qasm/" + fname

    # 3. save in the file
    write_string(qasm_string, path)
    write_depth(depth_entry + "\n")

    pass_type = None

    if pass_.is_analysis_pass:
        pass_type = "A"
        Overview.total_passes["A"] += 1
    else:
        pass_type = "T"
        Overview.total_passes["T"] += 1

    # make a box of properties
    if pass_type == "A":
        head = Headings.analyse_label_name(pass_.name())
    else:
        head = Headings.transform_label_name(pass_.name())

    # change
    time_taken = HTML(
        r"<p style ='" + Styles.time_button + "'>  " + str(round(time, 5)) + " ms </p>",
        layout=Layouts.button_layout1,
    )

    #     head_box = HBox([head], layout=Layouts.box_overview)

    # update the overview panel
    Overview.depths["final"] = dag.depth()
    Overview.op_count["final"] = len(dag.op_nodes(include_directives=False))

    props = [time_taken]

    one_q_ops, two_q_ops = 0, 0

    nodes = dag.op_nodes(include_directives=False)

    for node in nodes:
        if len(node.qargs) > 1:
            two_q_ops += 1
        else:
            one_q_ops += 1

    # 2. encapsulate BASIC circuit properties in Labels

    dag_properties = {
        "Width": dag.width(),
        "Size": dag.size(),
        "Depth": dag.depth(),
        "1-Q ops": one_q_ops,
        "2-Q ops": two_q_ops,
    }

    for prop, value in dag_properties.items():
        style = Styles.same_value

        if prop not in PreviousPass.circuit_props:
            pass  # here, each pass will always have this
        else:
            if value != PreviousPass.circuit_props[prop]:
                style = Styles.changed_value

        props.append(
            HTML(
                r"<p style = '"
                + style
                + "'> "
                + str(prop)
                + " : "
                + str(value)
                + " </p>",
                layout=Layouts.button_layout1,
            )
        )
        PreviousPass.circuit_props[prop] = value

    prop_box = HBox(children=props, layout=Layouts.box_layout_row)

    new_pass = VBox(
        [head, prop_box], layout=dict(display="flex", flex_flow="column", width="100%")
    )

    with main_view:
        display(new_pass)


class TreBugger:
    def __init__(self):
        self.__version = __qiskit_version__["qiskit"]
        self.__clear_view()

    def __clear_view(self):
        main_view.clear_output()

        PreviousPass.clear()

        Overview.clear()

        try:
            rmtree("debug-info/")
        except:
            pass
        makedirs("debug-info/")
        # clear depth and direectories
        open("debug-info/depth.txt", "w").close()  # clear the depth file
        makedirs("debug-info/images/")
        makedirs("debug-info/qpy/")
        makedirs("debug-info/qasm/")

    def __get_args_accordion(self, **kwargs):

        # make two boxes for each key and values
        key_box = {}
        val_box = {}
        for i in range(2):
            key_box[i] = VBox(layout=Layouts.box_kwargs)

            val_box[i] = VBox(layout=Layouts.box_kwargs)

        # make children dicts
        key_children = {0: [], 1: []}
        value_children = {0: [], 1: []}

        # get the length
        n = len(kwargs.items())

        # counter
        index = 0

        for i, (key, val) in enumerate(kwargs.items()):
            if val is None:
                continue

            # make key and value labels
            key_label = HTML(
                r"<p style = '" + Styles.key_style + "'><b> " + key + "</b></p>"
            )

            if get_size(val) < 2 ** 15:
                value = val
            else:
                value = "Value too large"

            value_label = HTML(
                r"<p style = '" + Styles.value_style + "'>" + str(value) + "</p>"
            )

            # add to the list
            key_children[index].append(key_label)
            value_children[index].append(value_label)

            # flip box id
            index = 0 if i < n // 2 else 1

        # construct the inner vertical boxes
        for i in range(2):
            key_box[i].children = key_children[i]
            val_box[i].children = value_children[i]

        # construct HBoxes
        args_box1 = HBox([key_box[0], val_box[0]], layout={"width": "50%"})
        args_box2 = HBox([key_box[1], val_box[1]], layout={"width": "50%"})

        # construct final HBox
        args_box = HBox([args_box1, args_box2])

        # construct Accordion
        args_acc = Accordion([args_box])
        args_acc.selected_index = None
        args_acc.set_title(0, "Params set for Transpiler")

        return args_acc

    def __get_overview_box(self):

        heading = HTML(
            "<h1 style = 'padding-top:6%; margin-left : 10%;'> Transpilation Overview</h1>"
        )
        transform = HTML(
            r"<p style = '"
            + Styles.label_transform
            + "'><b>  Transformation Passes  </b></p> <p style = '"
            + Styles.label_text
            + "'> "
            + str(Overview.total_passes["T"])
            + "</p>"
        )
        analyse = HTML(
            r"<p style = '"
            + Styles.label_analyse
            + "'><b>  Analysis Passes  </b></p> <p style = '"
            + Styles.label_text
            + "'> "
            + str(Overview.total_passes["A"])
            + "</p>"
        )

        init_depth = HTML(
            r"<p style = '"
            + Styles.label_purple_back
            + "'>  Initial depth  </p> <p style = '"
            + Styles.label_text
            + "'> "
            + str(Overview.depths["init"])
            + "</p>"
        )

        final_depth = HTML(
            r"<p style = '"
            + Styles.label_purple_back
            + "'> Final depth  </p> <p style = '"
            + Styles.label_text
            + "'> "
            + str(Overview.depths["final"])
            + "</p>"
        )

        init_ops = HTML(
            r"<p style = '"
            + Styles.label_purple_back
            + "'> Initial Op Count  </p> <p style = '"
            + Styles.label_text
            + "'> "
            + str(Overview.op_count["init"])
            + "</p>"
        )

        final_ops = HTML(
            r"<p style = '"
            + Styles.label_purple_back
            + "'>  Final Op Count </p> <p style = '"
            + Styles.label_text
            + "'> "
            + str(Overview.op_count["final"])
            + "</p>"
        )

        box1 = VBox([transform, init_depth, final_depth], layout=Layouts.box_overview)
        box2 = VBox([analyse, init_ops, final_ops], layout=Layouts.box_overview)

        overview = HBox(
            [heading, box1, box2], layout=dict(display="flex", flex_flow="row")
        )

        return overview

    def __make_description(self, backend, opt_level, **kwargs):

        backend_name = backend.name()

        # add the second child
        # this will also have an accordion with the labels set
        decription = HBox(
            [
                Button(
                    description=f"backend : {backend_name} ",
                    style=Styles.button_style1,
                    layout=Layouts.button_layout1,
                    disabled=True,
                ),
                Button(
                    description=f"qiskit version : qiskit v{self.__version} ",
                    style=Styles.button_style1,
                    layout=Layouts.button_layout1,
                    disabled=True,
                ),
                Button(
                    description=f"Optimization level : {opt_level}",
                    style=Styles.button_style1,
                    layout=Layouts.button_layout1,
                    disabled=True,
                ),
            ],
            layout=dict(display="flex", align_items="stretch", flex_flow="row"),
        )

        # generate the logo
        logo_uri = b64encode(open("imgs/logo_circ.gif", "rb").read()).decode("utf-8")
        img_tag = '<img height = 65px width = 65px src="data:image/png;base64,{0}">'.format(
            logo_uri
        )

        # make the HBox for accordion
        args = self.__get_args_accordion(**kwargs)

        # make the VBox for the overview
        overview = self.__get_overview_box()

        self.__debugger.children = [
            VBox(
                [
                    HTML(
                        "<p style = 'margin-left: 30px; color : #1b047c; font-size: 3em; text-align: center;'><b> Transpiler Debugger </b> &nbsp;"
                        + img_tag
                        + " </p> <hr>"
                    ),
                    decription,
                    args,
                    overview,
                    main_view,
                ],
                layout={"align-items": "space-around"},
            )
        ]
        self.__debugger.set_title(0, "TREBUGGER")
        self.__debugger.selected_index = None

    def debug(
        self,
        circuit,
        backend,
        optimization_level,
        debug_level,
        seed=None,
        disp=True,
        **kwargs,
    ):

        self.__debugger = Accordion()

        self.__clear_view()

        Overview.depths["init"] = circuit.depth()
        Overview.op_count["init"] = sum(
            [value for value in circuit.count_ops().values()]
        )

        if debug_level not in ["basic", "advanced"]:
            raise ValueError("Debug level must be one of ['basic','advanced']")

        if debug_level == "basic":
            callback = basic_callback
        else:
            callback = advanced_callback

        transpile(
            circuit,
            backend=backend,
            optimization_level=optimization_level,
            callback=callback,
            seed_transpiler=seed,
            **kwargs,
        )

        self.__make_description(backend, optimization_level, **kwargs)

        if disp:
            display(self.__debugger)
