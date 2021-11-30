from qiskit.converters import dag_to_circuit
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
            "stats": {
                "border": "1px inset #eee",
                "padding": "0",
                "height": "400px",
                "width": "20%",
            },
            "tabular_data": {
                "padding": "5px",
                "grid_template_columns": "repeat(2, 50%)",
            },
        }

        style = widgets.HTML(self._get_styles())
        header = widgets.HTML(
            '<div class=" widget-gridbox" style="height: 60px; width: 100%; grid-template-columns: auto 78px;"><div class=" title"><h1>Qiskit Timeline Debugger</h1></div><div class="logo"></div></div>'
        )

        general_info_panel = widgets.GridBox(children=[], layout={"width": "100%"})
        general_info_panel.add_class("options")

        # summary panel
        summary_panel = widgets.HBox(
            [], layout=dict(display="flex", flex_flow="row", margin="1% 2% 1% 1%")
        )

        # params panel
        param_button = widgets.Button(
            description="Params set for Transpiler",
            icon="caret-right",
            tooltip="Params for transpilation",
            layout={"width": "auto"},
        )
        # callback to add the box
        param_button.add_class("param-button")
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

        stats_wpr = widgets.VBox(
            children=[stats_title, stats_panel], layout=self.layouts["stats"]
        )

        main_panel = widgets.HBox(children=[timeline_wpr], layout={"width": "100%"})

        super(TimelineView, self).__init__(*args, **kwargs)
        self.children = (
            style,
            header,
            general_info_panel,
            params_panel,
            summary_panel,
            main_panel,
        )
        self.layout = {"width": "100%"}
        self.add_class("tp-widget")

        self.general_info_panel = general_info_panel
        self.summary_panel = summary_panel
        self.params_panel = params_panel

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
        self.summary_panel.children = self._get_summary_panel()

    def _get_summary_panel(self):

        heading = widgets.HTML(
            "<h2 style = 'padding-top:10%; margin-left : 13%;'> Transpilation Overview</h2>"
        )

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

        box_layout = dict(
            width="40%", display="flex", align_items="stretch", flex_flow="column"
        )
        box1 = widgets.VBox(
            [transform_head, init_depth, final_depth], layout=box_layout
        )
        box2 = widgets.VBox([analyse_head, init_ops, final_ops], layout=box_layout)

        overview_children = [heading, box1, box2]

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
            step_items,
            layout={
                "width": "100%",
                "grid_template_columns": "35px 44% 70px 70px 70px 70px 70px 70px",
                "min_height": "47px",
            },
        )
        item_wpr.add_class("transpilation-step")

        details_wpr = widgets.Box(layout={"width": "100%"})
        details_wpr.add_class("step-details")
        details_wpr.add_class("step-details-hide")

        self.timeline_panel.children = self.timeline_panel.children + (
            item_wpr,
            details_wpr,
        )

        self.select_step(step)

    def select_step(self, step):
        step_index = step.index

        for child in self.timeline_panel.children:
            child.remove_class("active")
        self.timeline_panel.children[step_index].add_class("active")

        # circuit stats:
        if step_index == 0:
            prev_stats = CircuitStats()
        else:
            prev_stats = self.transpilation_sequence.steps[step_index - 1].circuit_stats

        self.stats_labels[1].value = str(step.circuit_stats.ops_1q)
        self.stats_labels[3].value = str(step.circuit_stats.ops_2q)
        self.stats_labels[5].value = str(step.circuit_stats.ops_3q)
        self.stats_labels[7].value = str(step.circuit_stats.depth)
        self.stats_labels[9].value = str(step.circuit_stats.size)
        self.stats_labels[11].value = str(step.circuit_stats.width)

        if prev_stats.ops_1q != step.circuit_stats.ops_1q:
            self.stats_labels[1].add_class("highlight")
        else:
            self.stats_labels[1].remove_class("highlight")

        if prev_stats.ops_2q != step.circuit_stats.ops_2q:
            self.stats_labels[3].add_class("highlight")
        else:
            self.stats_labels[3].remove_class("highlight")

        if prev_stats.ops_3q != step.circuit_stats.ops_3q:
            self.stats_labels[5].add_class("highlight")
        else:
            self.stats_labels[5].remove_class("highlight")

        if prev_stats.depth != step.circuit_stats.depth:
            self.stats_labels[7].add_class("highlight")
        else:
            self.stats_labels[7].remove_class("highlight")

        if prev_stats.size != step.circuit_stats.size:
            self.stats_labels[9].add_class("highlight")
        else:
            self.stats_labels[9].remove_class("highlight")

        if prev_stats.width != step.circuit_stats.width:
            self.stats_labels[11].add_class("highlight")
        else:
            self.stats_labels[11].remove_class("highlight")

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

            if len(self._get_step_property_set(step)) == 0:
                tab.add_class("no-props")
            if len(step.logs) == 0:
                tab.add_class("no-logs")

        step = self.transpilation_sequence.steps[int(btn.value)]
        self.select_step(step)

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

                    for prop_name in _property_set:
                        property = _property_set[prop_name]
                        u = widgets.Label(value=property.name)
                        if (
                            type(property.value) == list
                            or type(property.value) == defaultdict
                        ):
                            txt = (
                                "(dict)"
                                if type(property.value) == defaultdict
                                else "(list)"
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
                        index = len(properties_panel.children)
                        properties_panel.children = properties_panel.children + (u, v)

                        u = widgets.Label(value=property.name)
                        if (
                            type(property.value) == list
                            or type(property.value) == defaultdict
                        ):
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

                disp_circ = CircuitComparator.compare(prev_circ, curr_circ)
                suffix = "diff_" + str(step_index)
            else:
                dag = self._get_step_dag(self.transpilation_sequence.steps[step_index])
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

        html_str = "<table>"
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
            for v in property.value:
                html_str = (
                    html_str
                    + "<tr><td><pre>"
                    + html.escape(str(v))
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
        img_data = b2a_base64(img_bio.getvalue()).decode()

        from qiskit.circuit import qpy_serialization

        qpy_bio = BytesIO()
        qpy_serialization.dump(disp_circuit, qpy_bio)
        qpy_data = b2a_base64(qpy_bio.getvalue()).decode()

        # qasm couldn't handle the circuit changed names

        # qasm_str = download_circ.qasm()
        # qasm_bio = BytesIO(bytes(qasm_str, "ascii"))
        # qasm_data = b2a_base64(qasm_bio.getvalue()).decode()

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
            </div>
            """

        return img_html

    def _get_step_dag(self, step):
        if step.type == PassType.TRANSFORMATION:
            return step.dag
        else:
            idx = step.index
            # Due to a bug in DAGCircuit.__eq__, we can not use ``step.dag != None``
            while not isinstance(
                self.transpilation_sequence.steps[idx].dag, DAGCircuit
            ):
                idx = idx - 1
                if idx < 0:
                    return None

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
        .title h1 { font-size: 37px; font-weight: bold; text-align: center; margin-top: 7px; }
        .logo { margin: 0 5px; background-position: center; background-repeat: no-repeat; background-size: contain; background-image: url(data:image/png;base64,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) }
        .step-details { min-height: 350px; background: #eee; }
        .step-details-hide { display: none !important; }

        .options { border-top: 1px solid #eee; }
        .options > div { font-size : 0.7 em; text-align: center; font-family: 'Roboto Mono', monospace; background: #eee; }

        .tp-widget { border:1px solid #aaa; }
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

        .transpilation-step { background: #fff; padding: 5px 0px 2px 0px; border-bottom: 1px solid #ddd; }
        .transpilation-step:hover { background: #eee; }
        .transpilation-step button { background: #fff; }
        .transpilation-step .transformation { 
                            color: cornsilk;
                            font-family : 'Lato';
                            padding: 3px 3px 3px 10px;
                            background-color: rgba(27, 4, 124, 0.7);
                            margin-right : 10%;
        }
        .transpilation-step .analysis { 
                        color: cornsilk; 
                        padding: 3px 3px 3px 10px;
                        font-family : 'Lato';
                        background-color: rgba(180, 77, 224, 0.7);
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

        .transpilation-step > :nth-child(2) { font-family: 'Roboto Mono', monospace; font-size: 16px; }
        .transpilation-step > :nth-child(3) { font-family: 'Roboto Mono', monospace; font-size: 10px; color: #900;}
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
        .param-button{
            padding: 5px 25px 10px 10px;
            font-size : 1.1em;
            height : 5%;
            text-align: left;
            background: #fff;
            transition: 0.5s;
            border: none !important;
        }
        .param-button:hover{
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
            margin-top : 10%;
            margin-left : 5%;
            color: cornsilk;
            padding: 15px 15px 15px 15px;
            font-size: 1.3em;
            background-color: rgba(27, 4, 124, 0.7);
        }
        
        .analyse-label {
            margin-top : 10%;
            margin-left : 5%;
            padding: 15px 15px 15px 15px;
            color: cornsilk;
            font-size: 1.3em;
            background-color: rgba(180, 77, 224, 0.7);
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
