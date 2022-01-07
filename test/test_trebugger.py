from seleniumbase import BaseCase
from elements import *


class DebuggerTests(BaseCase):

    # ordering is by lexicographic
    def test_a1_setup(self):
        self.open(SetUp.base)
        self.open(SetUp.URL)
        self.click(SetUp.kernel_link)
        self.click(SetUp.start_kernel)
        self.wait(1)
        self.click(SetUp.start_confirm)

        # wait for loading
        self.wait_for_element_present(SetUp.title)
        self.scroll_to_bottom()

    def test_a2_header(self):
        # test_ header
        self.assert_text("Qiskit Timeline Debugger", Header.head)
        self.assert_element(Header.logo)

    def test_a3_general_info(self):
        # test_ the information panel

        self.wait_for_element_present(GeneralInfo.terra_v)

        # text assertion
        self.assert_text("Backend: fake_casablanca", GeneralInfo.backend)
        self.assert_text("optimization_level: None", GeneralInfo.opt_level)
        self.assert_text("Qiskit", GeneralInfo.qiskit_v)
        self.assert_text("Terra version", GeneralInfo.terra_v)

    def test_a4_params(self):
        # wait for param button
        self.wait_for_element_present(Params.param_button)
        self.click(Params.param_button)

        # initial layout needs to be present

        self.assert_text("initial_layout", Params.key)
        self.assert_text("[0, 1]", Params.value)

    def test_a5_summary(self):
        self.wait_for_element_present(Summary.panel)

        # test_ the head

        self.assert_text("Transpilation Overview", Summary.header)

        self.wait_for_element_present(Summary.analyse_label)

        self.assert_text("Transformation Passes", Summary.transform_label)
        self.assert_text("Analysis Passes", Summary.analyse_label)

        # test_ label_stats
        self.wait_for_element_present(Summary.stat_path(1))

        self.assert_text("Initial depth", Summary.stat_path(1))
        self.assert_text("Final depth", Summary.stat_path(2))
        self.assert_text("Initial Op count", Summary.stat_path(3))
        self.assert_text("Final Op count", Summary.stat_path(4))

    def test_a6_passes(self):
        # test_ the name and click accordion

        self.wait_for_element_present(TimelinePanel.main_button)
        self.assert_text("Transpiler Passes", TimelinePanel.main_button)
        self.click(TimelinePanel.main_button)

    def test_a7_circuit_stats(self):
        # pick the first pass, check elements and click
        # here, the accordion must be expanded

        self.wait_for_element_present(TimelinePanel.step)

        self.assert_text("0 - SetLayout", TimelinePanel.pass_name)

        self.assert_text("0.0 ms", TimelinePanel.time_taken)

        i = 0
        for stat in TimelinePanel.stats:
            path1, path2 = TimelinePanel.get_stat(i, 1), TimelinePanel.get_stat(i, 2)

            self.assert_text(stat, path1)
            self.assert_text(TimelinePanel.stats[stat], path2)
            i += 1

        # check expansion
        self.click(TimelinePanel.pass_button)

    def test_a8_highlights(self):
        # choose a pass for testing highlights
        self.wait_for_element_present(TimelinePanel.highlight_step)

        # check if highlight class is present
        for element in TimelinePanel.highlights:
            class_val = self.get_attribute(element, "class")
            self.assert_in("highlight", class_val)

    def test_a9_tabs(self):
        # check the pass you clicked and check tabs

        for tab in TimelinePanel.tabs:
            self.click(tab["path"])
            if tab["name"] == "img":
                self.click(TimelinePanel.diff_link)

    def test_b1_download(self):

        # go to tab
        self.click(Downloads.circuit_img)

        for format in Downloads.formats:
            element = Downloads.formats[format]
            path = Downloads.base_path + element

            self.click(path)
            # self.assert_downloaded_file(
            #     "circuit_diff_0"+format, timeout=2)
