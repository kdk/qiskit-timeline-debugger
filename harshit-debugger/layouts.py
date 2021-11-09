from ipywidgets import Button, HTML
from gzip import GzipFile
from qiskit.circuit import QuantumCircuit, qpy_serialization


class Layouts:
    items_layout = dict(width="auto")

    box_layout = dict(
        display="flex",
        flex_flow="column",
        align_items="stretch",
        align_content="space-around",
        width="55%",
    )

    box_layout2 = dict(
        display="flex", flex_flow="column", align_items="stretch", width="100%"
    )
    box_layout_row = dict(display="flex", flex_flow="row", align_items="stretch")
    box_overview = dict(
        width="40%", display="flex", align_items="stretch", flex_flow="column"
    )

    box_layout_basic = dict(
        width="100%", display="flex", align_items="stretch", flex_flow="row"
    )

    acc_layout = dict(width="80%", margin="1.5% 0 1.5% 3%")

    acc_button = dict(width="auto", height="50px", display="center")

    output_layout = dict(
        display="flex",
        flex_flow="column",
        align_items="center",
        width="45%",
        border="1px solid",
    )

    button_layout1 = dict(width="100%", height="30px")
    button_layout2 = dict(width="15%", height="40px")


class Styles:

    same_value = """  margin: 3% 3% 3% 3%;
                    padding: 5px 5px 5px 5px;
                    color: cornsilk;
                    text-align: center;
                    opacity: 0.75;
                    background-color: #ca80e9; """

    changed_value = """  margin: 3% 3% 3% 3%;
                        padding: 5px 5px 5px 5px;
                        color: cornsilk;
                        text-align: center;
                        opacity: 0.75;
                        background-color: #1e002a; """

    button_style1 = dict(font_weight="bold", button_color="beige")

    button_style2 = dict(
        font_weight="bold", button_color="#d3bfe5", padding="4px 5px 5px 4px"
    )

    button_transform = dict(
        font_weight="bold", button_color="#1b047c", padding="2px 3px 3px 2px"
    )

    button_analyse = dict(
        font_weight="bold", button_color="#b44de0", padding="2px 3px 3px 2px"
    )

    diff_style = {"gatefacecolor": "grey", "gatetextcolor": "black"}

    label_purple_back = """
                        margin-left : 5%;
                        padding: 5px 0px 2px 15px;
                        font-size: 1.1em;
                        color: white;
                        background-color: #d499ed;"""

    label_analyse = """  margin-top : 10%;
                        margin-left : 5%;
                        padding: 15px 15px 15px 15px;
                        color: cornsilk;
                        font-size: 1.3em;
                        background-color: #b44de0; """

    label_analyse_inner = """  margin:  3% 3% 3% 3%;
                        padding: 10px 10px 10px 10px;
                        color: cornsilk;
                        text-align: center;
                        font-size: 1.2em;
                        background-color: #b44de0; """

    label_transform = """   margin-top : 10%;
                        margin-left : 5%;
                        color: cornsilk;
                        padding: 15px 15px 15px 15px;
                        font-size: 1.3em;
                        background-color: #1b047c;"""

    label_transform_inner = """   margin:  3% 3% 3% 3%;
                        color: cornsilk;
                        padding: 10px 10px 10px 10px;
                        text-align: center;
                        font-size: 1.2em;
                        background-color: #1b047c;"""

    label_text = " padding: 2px 2px 2px 2px; margin-left:10%; font-size: 1.1em;"


class Headings:
    transform_label = HTML(
        r"<p style = '"
        + Styles.label_transform_inner
        + "'><b>  Transformation Pass  </b></p>"
    )
    analyse_label = HTML(
        r"<p style = '" + Styles.label_analyse_inner + "'><b>  Analysis Pass  </b></p> "
    )

    def transform_label_name(text):
        return HTML(
            r"<p style = '"
            + Styles.label_transform_inner
            + "'><b>  "
            + text
            + "  </b></p>",
            layout=dict(width="auto"),
        )

    def analyse_label_name(text):
        return HTML(
            r"<p style = '"
            + Styles.label_analyse_inner
            + "'><b>  "
            + text
            + "  </b></p> ",
            layout=dict(width="auto"),
        )


class Download_Button(Button):
    def __init__(self, name, button_type, circuit, **kwargs):
        super(Download_Button, self).__init__(**kwargs)
        self.name = name
        self.circuit = circuit
        if button_type == "circ_img":
            self.on_click(self.__on_click_img)
        else:
            self.on_click(self.__on_click_qpy)

    # add observer method : this needs to have the
    # CURRENT circuit to save the diff
    def __on_click_img(self, b):

        # a circuit needs to be provided because we
        # want to save the diff image
        save_path = "debug-info/images/" + self.name + ".png"
        self.circuit.draw("mpl", filename=save_path, scale=0.8, style=Styles.diff_style)

    # save the qpy file of the pass
    def __on_click_qpy(self, b):

        save_path = "debug-info/qpy/" + self.name + ".qpy"
        with open(save_path, "wb") as fd:
            qpy_serialization.dump(self.circuit, fd)
