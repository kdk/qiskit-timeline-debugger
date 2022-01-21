import ipywidgets as widgets

class ButtonWithValue(widgets.Button):
    def __init__(self, *args, **kwargs):
        self.value = kwargs['value']
        kwargs.pop('value', None)
        super(ButtonWithValue, self).__init__(*args, **kwargs)