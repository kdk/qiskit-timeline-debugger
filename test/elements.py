class SetUp:
    base = "http://localhost:8890/"
    URL = "http://localhost:8890/notebooks/test/testing.ipynb"
    kernel_link = "#kernellink"
    start_kernel = "link=Restart & Run All"
    start_confirm = "(.//*[normalize-space(text()) and normalize-space(.)='Continue Running'])[1]/following::button[1]"
    title = '//div[@class=" title"]'


class Header:

    head = '//div[@class=" title"]/h1'
    logo = "//div[@class='logo']"


class GeneralInfo:
    # test the info headings
    base_path = "//div[contains(@class,'options')]"
    backend = base_path + "/div[1]"
    opt_level = base_path + "/div[2]"
    qiskit_v, terra_v = (base_path + "/div[3]"), (base_path + "/div[4]")


class Params:
    # check the params set for trebugger

    param_button = "//button[@title='Params for transpilation']"
    key = '//p[@class="params-key"]'
    value = '//p[@class="params-value"]'


class Summary:
    # check the summary headings
    # check the circuit stat headings
    panel = "//div[@id = 'notebook-container']/div/div[2]/div[2]/div/div[3]/div/div[5]"
    header = panel + "/div/div/h2"
    transform_label = "//p[@class='transform-label']"
    analyse_label = "//p[@class='analyse-label']"
    stats_base1 = "//div[@id='notebook-container']/div[1]/div[2]/div[2]/div/div[3]/div/div[5]/div[2]"
    stats_base2 = "/div/p[1]"

    @classmethod
    def stat_path(cls, num):
        num += 2  # starts from 3
        return cls.stats_base1 + f"/div[{num}]" + cls.stats_base2


class TimelinePanel:
    # general
    # a. Displaying list of passes
    main_button = '//*[@id="notebook-container"]/div[1]/div[2]/div[2]/div/div[3]/div/div[6]/button'
    # b. Displaying circuit stats for each pass

    step = "//*[@id='notebook-container']/div[1]/div[2]/div[2]/div/div[3]/div/div[6]/div/div/div/div[1]"
    pass_name = step + "/div[2]/div/p"
    time_taken = step + "/div[3]"

    stats = {"Depth": "4", "Size": "5", "Width": "4", "1Q ops": "3", "2Q ops": "1"}

    pass_button = step + "/div[1]/button"

    @classmethod
    def get_stat(cls, num, index):
        num += 4
        return cls.step + f"/div[{num}]/div/span[{index}]"

    # c. Highlight changed circuit stats

    # 2. Check the uncollapsed view with :
    diff_link = '//input[@title="Highlight diff"]'

    # a. Provide pass docs
    # b. Provide circuit plot
    # c. Provide log panel
    # d. Provide property set

    tabs = []
    names = ["img", "prop", "log", "doc"]
    for i in range(4):
        tabs.append({"name": names[i], "path": f"//li[@id='tab-key-{i}']"})

    # highlights
    highlight_step = '//*[@id="notebook-container"]/div[1]/div[2]/div[2]/div/div[3]/div/div[6]/div/div/div/div[19]'

    # divs 4,5 and 7 contain the highlights
    highlights = [
        highlight_step + "/div[4]",
        highlight_step + "/div[5]",
        highlight_step + "/div[7]",
    ]


class Downloads:

    circuit_img = "//li[@id='tab-key-0']"

    base_path = '//div[@class="circuit-export-wpr"]'

    # Provide download in qasm
    # provide download in qpy
    # provide download in img
    formats = {".png": "/a[1]", ".qpy": "/a[2]", ".qasm": "/a[3]"}
