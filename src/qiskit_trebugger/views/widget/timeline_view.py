from numpy import disp
from qiskit.converters import dag_to_circuit, circuit_to_dag
from qiskit.dagcircuit import DAGCircuit

from collections import defaultdict
from threading import Thread
from datetime import datetime
import html
import ipywidgets as widgets
from IPython.display import HTML

from .button_with_value import ButtonWithValue
from ...model.pass_type import PassType
from ...model.circuit_stats import CircuitStats
from ...model.circuit_comparator import CircuitComparator


class TimelineView(widgets.VBox):
    def __init__(self, *args, **kwargs):
        self.layouts = {
            "timeline": {
                "border": "1px #eee",
                "padding": "2px",
                "height": "400px",
                "overflow": "auto",
                "width": "100%",
            },
            "tabular_data": {
                "padding": "5px",
                "grid_template_columns": "repeat(2, 50%)",
            },
        }

        style = widgets.HTML(self._get_styles())
        header = widgets.HTML(
            '<div class=" widget-gridbox" style="width: 100%; grid-template-columns: auto 8%;"><div class=" title"><h1>Qiskit Timeline Debugger</h1></div><div class="logo"></div></div>'
        )

        general_info_panel = widgets.GridBox(children=[], layout={"width": "100%"})
        general_info_panel.add_class("options")

        # summary panel
        summary_heading = widgets.HTML(
            "<h2 style = 'margin: 10px 20px 0 30px; font-weight: bold;'> Transpilation Overview</h2>"
        )
        summary_panel = widgets.VBox(
            [
                summary_heading,
                widgets.GridBox(
                    [],
                    layout={
                        "width": "100%",
                        "padding": "5px",
                        "grid_template_columns": "repeat(2, 50%)",
                    },
                ),
            ],
            layout={"width": "100%"},
        )

        # params panel
        param_button = widgets.Button(
            description="Params set for Transpiler",
            icon="caret-right",
            tooltip="Params for transpilation",
            layout={"width": "auto"},
        )
        # callback to add the box
        param_button.add_class("toggle-button")
        param_button.on_click(self._add_args)

        params_panel = widgets.VBox([param_button], layout=dict(margin="0 1% 0 1%"))

        self.timeline_panel = widgets.VBox([], layout={"width": "100%"})
        timeline_wpr = widgets.Box(
            [self.timeline_panel], layout=self.layouts["timeline"]
        )

        stats_title = widgets.Label("Circuit Stats")
        stats_title.add_class("stats-title")

        self.stats_labels = [
            widgets.Label("1q ops"),
            widgets.Label(""),
            widgets.Label("2q ops"),
            widgets.Label(""),
            widgets.Label("3+q ops"),
            widgets.Label(""),
            widgets.Label("Depth"),
            widgets.Label(""),
            widgets.Label("Size"),
            widgets.Label(""),
            widgets.Label("Width"),
            widgets.Label(""),
        ]

        stats_panel = widgets.GridBox(
            self.stats_labels, layout=self.layouts["tabular_data"]
        )
        stats_panel.add_class("table")

        toggle_pass_button = widgets.Button(
            description="Transpiler Passes",
            icon="caret-right",
            tooltip="Transpiler Passes",
            layout={"width": "auto"},
        )
        toggle_pass_button.add_class("toggle-button")
        toggle_pass_button.on_click(self._load_passes)

        self.main_panel = widgets.HBox(
            children=[timeline_wpr], layout={"width": "100%"}
        )

        pass_panel = widgets.VBox([toggle_pass_button], layout=dict(margin="0 1% 0 1%"))

        super(TimelineView, self).__init__(*args, **kwargs)
        self.children = (
            style,
            header,
            general_info_panel,
            params_panel,
            summary_panel,
            pass_panel,
        )
        self.layout = {"width": "100%"}
        self.add_class("tp-widget")

        self.general_info_panel = general_info_panel
        self.summary_panel = summary_panel
        self.params_panel = params_panel
        self.pass_panel = pass_panel

        self._transpilation_sequence = None

    @property
    def transpilation_sequence(self):
        """Returns the transpilation_sequence object"""
        return self._transpilation_sequence

    @transpilation_sequence.setter
    def transpilation_sequence(self, transpilation_sequence):
        self._transpilation_sequence = transpilation_sequence

        # Set general info:
        items = []
        general_info = transpilation_sequence.general_info
        for key, value in general_info.items():
            items.append(widgets.Label(key + ": " + str(value)))
        self.general_info_panel.children = items
        self.general_info_panel.layout = {
            "width": "100%",
            "grid_template_columns": "repeat(" + str(len(general_info)) + ", auto)",
        }

    def update_summary(self):
        # update the summary panel after the transpilation
        # populates the tranpilation sequence
        self.summary_panel.children[1].add_class("summary-panel")
        self.summary_panel.children[1].children = self._get_summary_panel()

    def _get_summary_panel(self):

        # get the total count of passes
        total_passes = {"T": 0, "A": 0}

        for step in self.transpilation_sequence.steps:
            if step.type == PassType.TRANSFORMATION:
                total_passes["T"] += 1
            else:
                total_passes["A"] += 1

        transform_head = widgets.HTML(
            r"""<p class = 'transform-label'>
                <b> Transformation Passes  </b></p>
                <p class = 'label-text'>
                """
            + str(total_passes["T"])
            + "</p>"
        )

        analyse_head = widgets.HTML(
            r"""<p class = 'analyse-label'>
                <b> Analysis Passes  </b></p>
                <p class = 'label-text'>
                """
            + str(total_passes["A"])
            + "</p>"
        )

        init_step = self.transpilation_sequence.steps[0]
        final_step = self.transpilation_sequence.steps[-1]

        # build overview
        Overview = {"depths": {"init": 0, "final": 0}, "ops": {"init": 0, "final": 0}}

        # get the depths
        Overview["depths"]["init"] = init_step.circuit_stats.depth

        Overview["depths"]["final"] = final_step.circuit_stats.depth

        # get the op counts
        Overview["ops"]["init"] = (
            init_step.circuit_stats.ops_1q
            + init_step.circuit_stats.ops_2q
            + init_step.circuit_stats.ops_3q
        )

        Overview["ops"]["final"] = (
            final_step.circuit_stats.ops_1q
            + final_step.circuit_stats.ops_2q
            + final_step.circuit_stats.ops_3q
        )

        init_depth = widgets.HTML(
            r"<p class = 'label-purple-back'>"
            + "  Initial depth  </p> <p class = 'label-text'>"
            + str(Overview["depths"]["init"])
            + "</p>"
        )

        final_depth = widgets.HTML(
            r"<p class = 'label-purple-back'>"
            + "  Final depth  </p> <p class = 'label-text'>"
            + str(Overview["depths"]["final"])
            + "</p>"
        )

        init_ops = widgets.HTML(
            r"<p class = 'label-purple-back'>"
            + "  Initial Op count </p> <p class = 'label-text'>"
            + str(Overview["ops"]["init"])
            + "</p>"
        )

        final_ops = widgets.HTML(
            r"<p class = 'label-purple-back'>"
            + "  Final Op count </p> <p class = 'label-text'>"
            + str(Overview["ops"]["final"])
            + "</p>"
        )

        overview_children = [
            transform_head,
            analyse_head,
            init_depth,
            final_depth,
            init_ops,
            final_ops,
        ]

        return overview_children

    def _add_args(self, btn):
        # here, if the button has been clicked
        # change the caret and add the child
        param_children = list(self.params_panel.children)

        if len(param_children) == 1:
            param_children.append(self.kwargs_box)
            btn.icon = "caret-down"

        else:
            del param_children[-1]
            btn.icon = "caret-right"

        self.params_panel.children = param_children

    def update_params(self, **kwargs):
        self.kwargs_box = self._get_args_panel(**kwargs)

    def _get_args_panel(self, **kwargs):
        # make two boxes for each key and values
        key_box = {}
        val_box = {}

        box_kwargs = dict(
            width="50%", display="flex", align_items="stretch", flex_flow="column"
        )
        for i in range(2):
            key_box[i] = widgets.VBox(layout=box_kwargs)

            val_box[i] = widgets.VBox(layout=box_kwargs)

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
            key_label = widgets.HTML(r"<p class = 'params-key'><b> " + key + "</b></p>")

            value = val
            value_label = widgets.HTML(
                r"<p class = 'params-value'>" + str(value) + "</p>"
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
        args_box1 = widgets.HBox([key_box[0], val_box[0]], layout={"width": "50%"})
        args_box2 = widgets.HBox([key_box[1], val_box[1]], layout={"width": "50%"})

        # construct final HBox
        args_box = widgets.HBox(
            [args_box1, args_box2], layout=dict(margin="10px 0 0 15px")
        )
        return args_box

    def _load_passes(self, btn):

        pass_children = list(self.pass_panel.children)

        if len(pass_children) == 1:
            pass_children.append(self.main_panel)
            btn.icon = "caret-down"

        else:
            del pass_children[-1]
            btn.icon = "caret-right"

        self.pass_panel.children = pass_children

    def add_step(self, step):
        step_items = []

        _item = ButtonWithValue(
            value=str(step.index),
            description="",
            icon="caret-right",
            tooltip=step.type.value + " Pass",
            layout={"width": "11px"},
        )
        _item.on_click(self.on_pass)
        step_items.append(widgets.Box([_item]))

        _item = widgets.HTML(r"<p>" + str(step.index) + " - " + step.name + "</p>")
        _item.add_class(step.type.value.lower())
        step_items.append(_item)

        from math import log10

        if step.duration > 0:
            duration_font_size = 10
            duration_font_size = 10 + round(log10(step.duration))
            _item = widgets.Label(str(round(step.duration, 1)) + " ms")
            _item.add_class("fs" + str(duration_font_size))
        else:
            _item = widgets.Label("")
        step_items.append(_item)

        # circuit stats:
        if step.index == 0:
            prev_stats = CircuitStats()
        else:
            prev_stats = self.transpilation_sequence.steps[step.index - 1].circuit_stats

        _item = widgets.HTML(
            '<span class="stat-name">Depth </span><span class="stat-value">'
            + str(step.circuit_stats.depth)
            + "</span>"
        )
        if prev_stats.depth != step.circuit_stats.depth:
            _item.add_class("highlight")
        step_items.append(_item)

        _item = widgets.HTML(
            '<span class="stat-name">Size </span><span class="stat-value">'
            + str(step.circuit_stats.size)
            + "</span>"
        )
        if prev_stats.size != step.circuit_stats.size:
            _item.add_class("highlight")
        step_items.append(_item)

        _item = widgets.HTML(
            '<span class="stat-name">Width </span><span class="stat-value">'
            + str(step.circuit_stats.width)
            + "</span>"
        )
        if prev_stats.width != step.circuit_stats.width:
            _item.add_class("highlight")
        step_items.append(_item)

        _item = widgets.HTML(
            '<span class="stat-name">1Q ops </span><span class="stat-value">'
            + str(step.circuit_stats.ops_1q)
            + "</span>"
        )
        if prev_stats.ops_1q != step.circuit_stats.ops_1q:
            _item.add_class("highlight")
        step_items.append(_item)

        _item = widgets.HTML(
            '<span class="stat-name">2Q ops </span><span class="stat-value">'
            + str(step.circuit_stats.ops_2q)
            + "</span>"
        )
        if prev_stats.ops_2q != step.circuit_stats.ops_2q:
            _item.add_class("highlight")
        step_items.append(_item)

        item_wpr = widgets.GridBox(
            step_items, layout={"width": "100%", "min_height": "47px",},
        )
        item_wpr.add_class("transpilation-step")

        details_wpr = widgets.Box(layout={"width": "100%"})
        details_wpr.add_class("step-details")
        details_wpr.add_class("step-details-hide")

        self.timeline_panel.children = self.timeline_panel.children + (
            item_wpr,
            details_wpr,
        )

    def show_details(self, step_index, title, content, width):
        details_panel = self.timeline_panel.children[2 * step_index + 1]
        out = widgets.Output(layout={"width": "100%"})
        details_panel.children = (out,)

        if "step-details-hide" in details_panel._dom_classes:
            details_panel.remove_class("step-details-hide")

        html_str = """
        <div class="content-wpr">
            <div class="content">{content}</div>
        </div>
        """.format(
            title=title, content=content
        )

        out.append_display_data(HTML(html_str))

    # for the clicking of the button on the left of the pass panel
    def on_pass(self, btn):
        step_index = int(btn.value)
        step = self.transpilation_sequence.steps[step_index]

        # Toggle detailed view:
        details_panel = self.timeline_panel.children[2 * step_index + 1]
        if "step-details-hide" not in details_panel._dom_classes:
            details_panel.add_class("step-details-hide")
            btn.icon = "caret-right"
        else:
            details_panel.remove_class("step-details-hide")
            btn.icon = "caret-down"

        if len(details_panel.children) == 0:

            # First time to expand this panel
            tab_titles = ["Circuit", "Property Set", "Logs", "Help"]
            children = [
                widgets.VBox(layout={"width": "100%"}),
                widgets.HBox(
                    children=[
                        widgets.GridBox(
                            [],
                            layout={
                                "width": "50%",
                                "padding": "5px",
                                "grid_template_columns": "repeat(2, 50%)",
                            },
                        ),
                        widgets.Output(layout={"width": "50%"}),
                    ],
                    layout={"width": "100%"},
                ),
                widgets.Output(layout={"width": "100%"}),
                widgets.Output(layout={"width": "100%"}),
            ]

            tab = widgets.Tab(model_id=str(step_index), layout={"width": "100%"})
            tab.children = children
            [tab.set_title(idx, name) for idx, name in enumerate(tab_titles)]
            details_panel.children = (tab,)

            dag = self._get_step_dag(step)

            # this is for the default one
            # when a tab is clicked, we would need to show something right

            # vars : tab, dag, index that's it
            # img_thread = Thread(target=self._load_img_view, args=[dag, tab, step_index])

            # img_thread.start()
            self._load_img_view(dag, tab, step_index)

            tab.observe(self.on_tab_clicked)

            children[1].children[0].add_class("property-set")
            children[1].children[1].add_class("property-items")

            if len(self._get_step_property_set(step)) == 0:
                tab.add_class("no-props")
            if len(step.logs) == 0:
                tab.add_class("no-logs")

    def _load_img_view(self, dag, tab, step_index):

        if isinstance(dag, DAGCircuit):

            img_wpr = widgets.Output(layout={"width": "100%"})
            img_wpr.append_display_data(HTML(self._get_spinner_html()))

            circ = dag_to_circuit(dag)
            img_html = self._view_circuit(circ, "after_pass_" + str(step_index))
            img_wpr.outputs = []
            img_wpr.append_display_data(HTML(img_html))

            diff_chk = widgets.Checkbox(
                model_id="step:" + str(step_index),
                value=False,
                description="Highlight diff",
                indent=False,
            )
            diff_chk.observe(self.on_diff)

            tab.children[0].children = (diff_chk, img_wpr)

        else:
            message = widgets.Label(
                value="Displaying circuits with depth larger than 300 is not supported!"
            )
            message.add_class("message")
            tab.children[0].children = (message,)

    def on_tab_clicked(self, change):
        if change["type"] == "change" and change["name"] == "selected_index":
            tabs = change.owner
            step_index = int(tabs.model_id)
            # get the transpiler pass which is displayed
            step = self.transpilation_sequence.steps[step_index]

            if change["new"] == 1:
                properties_panel = tabs.children[1].children[0]

                # If content is already rendered, do nothing:
                if (
                    type(tabs.children[1].children[0]) == widgets.Label
                    or len(properties_panel.children) > 0
                ):
                    return

                _property_set = self._get_step_property_set(step)
                if len(_property_set) > 0:
                    properties_panel.add_class("table")
                    panel_height = {}
                    properties_panel.layout = {
                        "width": "50%",
                        "padding": "5px",
                        "grid_template_columns": "repeat(2, 50%)",
                        "height": str(33 * len(_property_set)) + "px",
                    }

                    for prop_name in _property_set:
                        property = _property_set[prop_name]
                        u = widgets.Label(value=property.name)
                        if property.type not in (int, float, bool, str):
                            txt = (
                                "(dict)"
                                if type(property.value) == defaultdict
                                else "(" + property.type.__name__ + ")"
                            )
                            prop_label = widgets.Label(txt, layout={"width": "80%"})
                            prop_button = ButtonWithValue(
                                value=None, description="...", layout={"width": "20%"}
                            )
                            prop_button.on_click(self.on_property)
                            v = widgets.HBox(
                                [prop_label, prop_button], layout={"width": "100%"}
                            )
                        else:
                            v = widgets.Label(value=str(property.value))

                        if step.property_set_index == step.index:
                            if property.state != "updated":
                                u.add_class(property.state)
                            v.add_class(property.state)

                        index = len(properties_panel.children)
                        properties_panel.children = properties_panel.children + (u, v)

                        if property.type not in (int, float, bool, str):
                            properties_panel.children[index + 1].children[1].value = (
                                str(step.index) + "," + property.name
                            )
                        else:
                            properties_panel.children[index + 1].value = str(
                                property.value
                            )

                    dd = list(properties_panel.children)
                    for m in range(int(len(dd) / 2)):
                        if properties_panel.children[2 * m].value not in _property_set:
                            properties_panel.children[2 * m].add_class("not-exist")
                            properties_panel.children[2 * m + 1].add_class("not-exist")
                        else:
                            properties_panel.children[2 * m].remove_class("not-exist")
                            properties_panel.children[2 * m + 1].remove_class(
                                "not-exist"
                            )
                else:
                    message = widgets.Label(value="Property set is empty!")
                    message.add_class("message")
                    tabs.children[1].children = (message,)

            elif change["new"] == 2:
                # for the Logs tab of the debugger

                # If content is already rendered, do nothing:
                if len(tabs.children[2].outputs) > 0:
                    return

                logs = step.logs
                if len(logs) > 0:
                    html_str = '<div class="logs-wpr">'
                    for entry in logs:
                        html_str = (
                            html_str
                            + "<pre class='date'>{0}</pre><pre class='level {1}'>[{1}]</pre><pre class='log-entry {1}'>{2}</pre>".format(
                                datetime.fromtimestamp(entry.time).strftime(
                                    "%H:%M:%S.%f"
                                )[:-3],
                                entry.levelname,
                                entry.msg % entry.args,
                            )
                        )
                    html_str = html_str + "</div>"
                    tabs.children[2].append_display_data(HTML(html_str))
                else:
                    html_str = '<div class="message">This pass does not write any log messages!</div>'
                    tabs.children[2].append_display_data(HTML(html_str))

            elif change["new"] == 3:
                # this is the docs tab

                # If content is already rendered, do nothing:
                if len(tabs.children[3].outputs) > 0:
                    return

                html_str = '<pre class="help">' + step.docs + "</pre>"
                html_str = (
                    html_str
                    + '<div class="help-header"><span style="color: #e83e8c;">'
                    + step.name
                    + '</span>.run(<span style="color: #0072c3;">dag</span>)</div>'
                )
                html_str = (
                    html_str + '<pre class="help">' + step.run_method_docs + "</pre>"
                )
                tabs.children[3].append_display_data(HTML(html_str))

    def on_diff(self, change):
        if (
            change["type"] == "change"
            and type(change["new"]) == dict
            and "value" in change["new"]
        ):
            chk = change.owner
            dummy, step_index_str = chk.model_id.split(":")
            step_index = int(step_index_str)

            details_panel = self.timeline_panel.children[2 * int(step_index) + 1]
            img_wpr = details_panel.children[0].children[0].children[1]
            img_wpr.outputs = []
            img_wpr.append_display_data(
                HTML(self._get_spinner_html())
            )  # to get the loader gif

            if change["new"]["value"]:
                if step_index > 0:
                    prev_dag = self._get_step_dag(
                        self.transpilation_sequence.steps[step_index - 1]
                    )
                    prev_circ = dag_to_circuit(prev_dag)
                else:
                    prev_circ = None

                curr_dag = self._get_step_dag(
                    self.transpilation_sequence.steps[step_index]
                )
                curr_circ = dag_to_circuit(curr_dag)

                # okay so this is basically the circuit diff class

                fully_changed, disp_circ = CircuitComparator.compare(
                    prev_circ, curr_circ
                )

                if fully_changed:
                    chk.description = "Circuit changed fully"
                    chk.disabled = True

                suffix = "diff_" + str(step_index)
            else:
                if not chk.disabled:
                    dag = self._get_step_dag(
                        self.transpilation_sequence.steps[step_index]
                    )
                    disp_circ = dag_to_circuit(dag)
                    suffix = "after_pass_" + str(step_index)

            # here, qasm and qpy need the without diff circuits
            img_html = self._view_circuit(disp_circ, suffix)
            img_wpr.outputs = []
            img_wpr.append_display_data(HTML(img_html))

    def on_property(self, btn):

        import warnings

        warnings.filterwarnings(
            "ignore",
            message="Back-references to from Bit instances to their containing Registers have been deprecated. Instead, inspect Registers to find their contained Bits.",
        )

        step_index, property_name = btn.value.split(",")

        details_panel = self.timeline_panel.children[2 * int(step_index) + 1]
        prop_details_panel = details_panel.children[0].children[1].children[1]

        step = self.transpilation_sequence.steps[int(step_index)]
        property_set = self._get_step_property_set(step)
        property = property_set[property_name]

        html_str = '<table style="width: 100%">'
        html_str = (
            html_str
            + '<thead><tr><th colspan="'
            + ("2" if type(property.value) == defaultdict else "1")
            + '">'
            + property_name
            + "</th></tr></thead>"
        )
        if property_name == "block_list":
            for v in property.value:
                v_arr = []
                for node in v:
                    qargs = ", ".join(
                        [
                            qarg.register.name
                            + "<small>["
                            + str(qarg.index)
                            + "]</small>"
                            for qarg in node.qargs
                        ]
                    )
                    v_arr.append(
                        "<strong>" + node.name + "</strong>" + "(" + qargs + ")"
                    )
                html_str = html_str + "<tr><td>" + " - ".join(v_arr) + "</td></tr>"
        elif property_name == "commutation_set":
            for key, v in property.value.items():
                key_str = ""
                if type(key) is tuple:
                    qargs = ", ".join(
                        [
                            qarg.register.name
                            + "<small>["
                            + str(qarg.index)
                            + "]</small>"
                            for qarg in key[0].qargs
                        ]
                    )
                    key_str = (
                        "(<strong>"
                        + (key[0].name if key[0].name != None else "")
                        + "</strong>("
                        + qargs
                        + "), "
                    )
                    key_str = (
                        key_str
                        + key[1].register.name
                        + "<small>["
                        + str(key[1].index)
                        + "]</small>"
                        + ")"
                    )
                else:
                    key_str = (
                        key.register.name + "<small>[" + str(key.index) + "]</small>"
                    )

                value_str = ""
                if type(v) is list:
                    value_str = value_str + "["
                    for nodes in v:
                        if type(nodes) is list:
                            nodes_arr = []
                            for node in nodes:
                                if node.type == "op":
                                    qargs = ", ".join(
                                        [
                                            qarg.register.name
                                            + "<small>["
                                            + str(qarg.index)
                                            + "]</small>"
                                            for qarg in node.qargs
                                        ]
                                    )
                                    node_str = (
                                        "<strong>"
                                        + (node.name if node.name != None else "")
                                        + "</strong>"
                                        + "("
                                        + qargs
                                        + ")"
                                    )
                                else:
                                    node_str = (
                                        node.type.upper()
                                        + "(wire="
                                        + node.wire.register.name
                                        + "<small>["
                                        + str(node.wire.index)
                                        + "]</small>)"
                                    )

                                nodes_arr.append(node_str)

                            value_str = (
                                value_str + "[" + (", ".join(nodes_arr)) + "]<br>"
                            )
                    value_str = value_str + "]"

                html_str = (
                    html_str
                    + '<tr><td style="width:50%">'
                    + key_str
                    + "</td><td><pre>"
                    + value_str
                    + "</pre></td></tr>"
                )
        else:
            html_str = (
                html_str
                + "<tr><td><pre>"
                + html.escape(str(property.value))
                + "</pre></td></tr>"
            )
        html_str = html_str + "</table>"

        prop_details_panel.outputs = []
        prop_details_panel.append_display_data(HTML(html_str))

    def _view_circuit(self, disp_circuit, suffix):
        from io import BytesIO
        from binascii import b2a_base64

        if "diff" in suffix:
            # means checkbox has been chosen for diff
            img_style = {"gatefacecolor": "orange", "gatetextcolor": "black"}

        else:
            img_style = None

        fig = disp_circuit.draw(
            "mpl",
            idle_wires=False,
            with_layout=False,
            scale=0.9,
            fold=20,
            style=img_style,
        )

        img_bio = BytesIO()
        fig.savefig(img_bio, format="png", bbox_inches="tight")
        fig.clf()
        img_data = b2a_base64(img_bio.getvalue()).decode()

        from qiskit.circuit import qpy_serialization

        qpy_bio = BytesIO()
        qpy_serialization.dump(disp_circuit, qpy_bio)
        qpy_data = b2a_base64(qpy_bio.getvalue()).decode()

        # qasm couldn't handle the circuit changed names

        for instr in disp_circuit.data:
            instr[0].name = instr[0].name.strip()

        qasm_str = disp_circuit.qasm()
        qasm_bio = BytesIO(bytes(qasm_str, "ascii"))
        qasm_data = b2a_base64(qasm_bio.getvalue()).decode()

        img_html = f"""
            <div class="circuit-plot-wpr">
                <img src="data:image/png;base64,{img_data}&#10;">
            </div>
            <div class="circuit-export-wpr">
                Save:
                <a download="circuit_{suffix}.png" href="data:image/png;base64,{img_data}" download>
                    <i class="fa fa-download"></i> <span>PNG</span>
                </a>
                <a download="circuit_{suffix}.qpy" href="data:application/octet-stream;base64,{qpy_data}" download>
                    <i class="fa fa-download"></i> <span>QPY</span>
                </a>
                <a download="circuit_{suffix}.qasm" href="data:application/octet-stream;base64,{qasm_data}" download>
                    <i class="fa fa-download"></i> <span>QASM</span>
                </a>
            </div>
            """

        return img_html

    def _get_step_dag(self, step):
        if step.type == PassType.TRANSFORMATION:
            return step.dag
        else:
            idx = step.index
            # Due to a bug in DAGCircuit.__eq__, we can not use ``step.dag != None``

            found_transform = False
            while (
                not isinstance(self.transpilation_sequence.steps[idx].dag, DAGCircuit)
                and idx > 0
            ):
                idx = idx - 1
                if idx >= 0:
                    found_transform = (
                        self.transpilation_sequence.steps[idx].type
                        == PassType.TRANSFORMATION
                    )

            if found_transform == False:
                return circuit_to_dag(self.transpilation_sequence.original_circuit)

            return self.transpilation_sequence.steps[idx].dag

    def _get_step_property_set(self, step):
        if step.property_set_index != None:
            return self.transpilation_sequence.steps[
                step.property_set_index
            ].property_set
        else:
            return {}

    def _get_spinner_html(self):
        return '<div class="lds-spinner"><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div></div>'

    def _get_styles(self):
        return """
        <style>
        .title h1 { font-size: 45px; font-weight: bold; text-align: center; padding: 10px 10px 10px 10px; }
        .logo { margin: 0 15px; background-position: center; background-repeat: no-repeat; background-size: contain; background-image: url('data:image/png;base64,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')}        
        .step-details { min-height: 350px; background: #eee; }
        .step-details-hide { display: none !important; }

        .options { border-top: 1px solid #eee; }
        .options > div { font-size : 0.7 em; text-align: center; font-family: 'Roboto Mono', monospace; background: #eee; }

        .tp-widget { border:1px solid #aaa; min-width: 300px; }
        .p-TabPanel-tabContents { padding: 5px !important; }
        .p-Collapse-header { padding: 1px 5px; background: #eee; }
        .p-Collapse-open > .p-Collapse-header { background: #ddd; }
        .p-Collapse-contents { padding-top: 0; padding-left: 0; padding-bottom: 0; padding-right: 0; height: 220px; background: #f5f5f5; }
        .p-Collapse-contents button {
            width: 20%;
            background: #fff;
            text-align: center;
            padding: 0;
            font-weight: bold; }


        div.output_scroll { box-shadow: none }

        .widget-gridbox.table { background: #f5f5f5; }
        .widget-gridbox.table .widget-label {
            background-color: #fff;
            padding: 0 3px;
            font-family: 'Open Sans', monospace;
            font-size: 14px;
        }

        .exist { font-weight: bold; }
        .not-exist { display: none; }

        .stats-title {
            background: #eee;
            margin: 0;
            text-align: center;
            font-size: 15px;
            font-weight: bold;
            font-family: 'Roboto Mono', monospace; }

        .widget-label.new, .widget-hbox.new .widget-label { font-weight: bold; color: #4b7bec; }
        .widget-label.updated, .widget-hbox.updated .widget-label { font-weight: bold; color: #e74c3c; }

        .transpilation-step {
            background: #fff;
            padding-top: 5px;
            border-bottom: 1px solid #ddd;
            grid-template-columns: 35px auto 70px 70px 70px 70px 70px 70px;
        }
        .transpilation-step:hover { background: #eee; }
        .transpilation-step button { background: #fff; }
        .transpilation-step .transformation {
                            color: cornsilk;
                            font-family : 'Lato';
                            padding: 3px 3px 3px 10px;
                            background-color: rgba(0, 67, 206, 0.8);
                            margin-right : 10%;
        }
        .transpilation-step .analysis {
                        color: cornsilk;
                        padding: 3px 3px 3px 10px;
                        font-family : 'Lato';
                        background-color: rgba(180, 77, 224, 0.8);
                        margin-right: 10%;
        }

        .transpilation-step div.fs10 { font-size: 10px; }
        .transpilation-step div.fs11 { font-size: 11px; }
        .transpilation-step div.fs12 { font-size: 12px; }
        .transpilation-step div.fs13 { font-size: 13px; }
        .transpilation-step div.fs14 { font-size: 14px; }
        .transpilation-step div.fs15 { font-size: 15px; }
        .transpilation-step > :nth-child(1) button { width: 11px; font-size: 20px; background: transparent; outline: 0 !important; border: none !important; }
        .transpilation-step > :nth-child(1) button:hover { border: none !important; outline: none !important; box-shadow: none !important; }
        .transpilation-step > :nth-child(1) button:focus { border: none !important; outline: none !important; box-shadow: none !important; }

        .transpilation-step.active > :nth-child(2) { font-weight: bold; }

        .transpilation-step > :nth-child(2) {
            font-family: 'Roboto Mono', monospace;
            font-size: 16px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .transpilation-step > :nth-child(3) { font-family: 'Roboto Mono', monospace; font-size: 10px; color: #900; text-align: right; }
        .transpilation-step > :nth-child(4) { font-family: 'Roboto Mono', monospace; text-align: center; }
        .transpilation-step > :nth-child(5) { font-family: 'Roboto Mono', monospace; text-align: center; }
        .transpilation-step > :nth-child(6) { font-family: 'Roboto Mono', monospace; text-align: center; }
        .transpilation-step > :nth-child(7) { font-family: 'Roboto Mono', monospace; text-align: center; }
        .transpilation-step > :nth-child(8) { font-family: 'Roboto Mono', monospace; text-align: center; }

        .stat-name { font-size: 10px; color: #aaa; }
        .stat-value { font-size: 12px; color: #000; }
        .highlight .stat-value { font-weight: bold; color: #e74c3c; }

        .logs-wpr { display: grid; grid-template-columns: 70px 60px auto; }
        .logs-wpr pre.date { font-size: 10px; }
        .logs-wpr pre.level { font-size: 10px; text-align: right; padding-right: 5px; }
        .logs-wpr pre.log-entry { font-size: 12px; }
        .logs-wpr pre.DEBUG { color: #000000; }
        .logs-wpr pre.INFO { color: #1c84a2; }
        .logs-wpr pre.WARNING { color: #ed7723; }
        .logs-wpr pre.ERROR { color: #d64e4a; }
        .logs-wpr pre.CRITICAL { color: white; background: #d64e4a; }

        div.output_area pre.help { font-family: Helvetica,Arial,sans-serif; font-size: 13px;
            border: 1px solid #ccc; padding: 10px;}
        div.help-header {
            font-family: 'Roboto Mono', monospace;
            font-size: 12px;
            border: 1px solid #ccc;
            border-bottom: none;
            margin-top: 4px;
            padding: 5px 10px;
            font-weight: bold;
            background: #f5f5f5;
        }
        .toggle-button{
            padding: 5px 25px 10px 10px;
            font-size : 1.1em;
            height : 5%;
            text-align: left;
            background: #fff;
            transition: 0.5s;
            border: none !important;
        }
        .toggle-button:hover{
            background: #eee;
            border: none;
            transition: 1s;
        }
        .params-key{
            margin: 2% 1% 1% 4%;
            padding: 5px 20px 5px 20px;
            font-size: 1em;
            color: cornsilk;
            background: rgba(15,23,229,0.7);
        }

        .params-value{
            margin: 1% 1% 1% 1%;
            padding: 5px 20px 5px 20px;
            border-left : 2px solid black;
            font-size: 1.1em;
        }

        .transform-label {
            margin-left : 5%;
            color: cornsilk;
            padding: 10px 15px 10px 15px;
            font-size: 1.3em;
            background-color: rgba(0, 67, 206, 0.8);
        }

        .analyse-label {
            margin-left : 5%;
            padding: 10px 15px 10px 15px;
            color: cornsilk;
            font-size: 1.3em;
            background-color: rgba(180, 77, 224, 0.8);
        }

        .label-text{
            padding: 2px 2px 2px 2px; margin-left:10%; font-size: 1.1em;
        }

        .label-purple-back{
            margin-left : 5%;
            padding: 5px 0px 2px 15px;
            font-size: 1.2em;
            color : #444444;
            background-color: rgba(245,174,230,0.4);
        }


        .content-wpr {
            overflow:hidden;
        }

        .content { overflow-y: auto; height: 325px; margin: 0; padding: 0; }
        .p-TabPanel-tabContents td { text-align: left; font-family: 'Roboto Mono', monospace; }
        .p-TabPanel-tabContents th { text-align: center; font-family: 'Roboto Mono', monospace; font-size: 14px; }

        .circuit-plot-wpr { height: 225px; overflow: auto; border: 1px solid #aaa; }
        .circuit-plot-wpr img { max-width: none; }
        .circuit-export-wpr a {
            display: inline-block;
            margin: 5px 2px;
            padding: 2px 15px;
            color: #000;
            background: #ddd;
            border: 1px solid transparent;
            text-decoration: none !important;
        }
        .circuit-export-wpr a:hover { border-color: #aaa; }

        .p-TabBar-tabIcon:before { font: normal normal normal 14px/1 FontAwesome; padding-right: 5px; }
        .p-TabBar-content > :nth-child(1) .p-TabBar-tabIcon:before { content: "\\f1de"; color: #b587f7; }
        .p-TabBar-content > :nth-child(2) .p-TabBar-tabIcon:before { content: "\\f00a"; color: #b33771; }
        .p-TabBar-content > :nth-child(3) .p-TabBar-tabIcon:before { content: "\\f039"; color: #ff9d85; }
        .p-TabBar-content > :nth-child(4) .p-TabBar-tabIcon:before { content: "\\f05a"; color: #6ea2c9; }

        .no-props .p-TabBar-content > :nth-child(2) .p-TabBar-tabLabel,
        .no-props .p-TabBar-content > :nth-child(2) .p-TabBar-tabIcon:before { color: #aaa; }
        .no-logs .p-TabBar-content > :nth-child(3) .p-TabBar-tabLabel,
        .no-logs .p-TabBar-content > :nth-child(3) .p-TabBar-tabIcon:before { color: #aaa; }

        .message { width: 90%; font-size: 26px; text-align: center; margin: 70px 0; font-weight: bold;}

        @media (max-width: 1000px) {
            .options { grid-template-columns: repeat(3, auto) !important; }
            .options > :nth-child(4) { display: none; }

            .transpilation-step { grid-template-columns: 35px auto 70px 70px 70px 70px 70px; }
            .transpilation-step > :nth-child(2) { font-size: 12px !important; }
            .transpilation-step > :nth-child(3) { display: none; }
        }

        @media (max-width:985px) {
            .title h1 { font-size: 26px; }
            .logo {margin : 0px 2px;}
            .transpilation-step { grid-template-columns: 35px auto 70px 70px 70px 70px; }
            .transpilation-step > :nth-child(6) { display: none; }

        }

        @media (max-width:800px) {
            
            
            .options { grid-template-columns: repeat(2, auto) !important; }
            .options > :nth-child(3) { display: none; }

            .transpilation-step { grid-template-columns: 35px auto 70px 70px 70px; }
            .transpilation-step > :nth-child(7) { display: none; }
        }

        @media (max-width:700px) {
            
            .summary-panel { grid-template-columns: repeat(1, auto) !important; }

            .property-set { width: 100% !important; }
            .property-items { display: none !important; }

            .circuit-export-wpr a {
                font-size: 12px;
                padding: 2px 6px;
            }

            .transpilation-step { grid-template-columns: 35px auto 70px 70px; }
            .transpilation-step > :nth-child(5) { display: none; }
        }

        @media (max-width:550px) {
             .logo {display: none;}
             .title {font-size : 14px;}
            .transpilation-step { grid-template-columns: 35px auto; }
            .transpilation-step > :nth-child(4) { display: none; }
            .transpilation-step > :nth-child(8) { display: none; }
        }

        .lds-spinner {
            position: relative;
            width: 80px;
            height: 80px;
            margin: 50px auto;
        }
        .lds-spinner div {
            transform-origin: 40px 40px;
            animation: lds-spinner 1.2s linear infinite;
        }
        .lds-spinner div:after {
            content: " ";
            display: block;
            position: absolute;
            top: 3px;
            left: 37px;
            width: 6px;
            height: 18px;
            border-radius: 20%;
            background: #aaa;
        }
        .lds-spinner div:nth-child(1) {
            transform: rotate(0deg);
            animation-delay: -1.1s;
        }
        .lds-spinner div:nth-child(2) {
            transform: rotate(30deg);
            animation-delay: -1s;
        }
        .lds-spinner div:nth-child(3) {
            transform: rotate(60deg);
            animation-delay: -0.9s;
        }
        .lds-spinner div:nth-child(4) {
            transform: rotate(90deg);
            animation-delay: -0.8s;
        }
        .lds-spinner div:nth-child(5) {
            transform: rotate(120deg);
            animation-delay: -0.7s;
        }
        .lds-spinner div:nth-child(6) {
            transform: rotate(150deg);
            animation-delay: -0.6s;
        }
        .lds-spinner div:nth-child(7) {
            transform: rotate(180deg);
            animation-delay: -0.5s;
        }
        .lds-spinner div:nth-child(8) {
            transform: rotate(210deg);
            animation-delay: -0.4s;
        }
        .lds-spinner div:nth-child(9) {
            transform: rotate(240deg);
            animation-delay: -0.3s;
        }
        .lds-spinner div:nth-child(10) {
            transform: rotate(270deg);
            animation-delay: -0.2s;
        }
        .lds-spinner div:nth-child(11) {
            transform: rotate(300deg);
            animation-delay: -0.1s;
        }
        .lds-spinner div:nth-child(12) {
            transform: rotate(330deg);
            animation-delay: 0s;
        }
        @keyframes lds-spinner {
            0% { opacity: 1; }
            100% { opacity: 0; }
        }
        </style>
        """
