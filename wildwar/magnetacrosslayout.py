'''
Based on kivy.garden.magnet
'''

from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty


class MagnetAcrossLayout(Widget):
    r''''''
    duration = NumericProperty(1)

    def __init__(self, *, actual_parent, transition_dict=None, **kwargs):
        super().__init__(**kwargs)
        self._transition_dict = (
            {'pos': 'out_quad', 'size': 'linear'}
            if transition_dict is None else transition_dict.copy())
        self._animations = []
        self._actual_parent = actual_parent
        self._child = None
        self.bind(**{key: self.attract for key in self._transition_dict})

    def add_widget(self, widget, **args):
        if self._actual_parent is None:
            raise ValueError(
                "You must set 'actual_parent' property"
                " before 'add_widget'.")
        else:
            pass
        if self._child is None:
            self._child = widget
            self._actual_parent.add_widget(widget)
        else:
            raise ValueError('MagnetAcrossLayout can have only one children')

    def remove_widget(self, widget):
        if self._child is widget:
            self._actual_parent.remove_widget(widget)
            self._child = None
        else:
            raise ValueError('Thats not my child.')

    def on_parent(self, __, parent):
        self.property('pos').dispatch(self)
        self.property('size').dispatch(self)

    def attract(self, *args):
        if self._child is None:
            return

        if self._animations:
            for animation in self._animations:
                animation.stop(self._child)
            self._animations = []

        for property_name in self._transition_dict.keys():
            if property_name == 'pos':
                animation = Animation(
                    transition=self._transition_dict['pos'],
                    duration=self.duration,
                    pos=self._actual_parent.to_widget(*self.to_window(*self.pos))
                )
            else:
                animation = Animation(
                    transition=self._transition_dict[property_name],
                    duration=self.duration,
                    **{property_name: getattr(self, property_name), })

            animation.start(self._child)
            self._animations.append(animation)


def _test():
    import random
    from kivy.base import runTouchApp
    from kivy.lang import Builder
    from kivy.factory import Factory
    from kivy.properties import ListProperty
    import kivy.utils

    Builder.load_string(r'''
<Card>:
    font_size: 50
    canvas.before:
        Color:
            rgba: .3, .3, .3, 1
        RoundedRectangle
            size: self.size
            pos: self.pos
        Color:
            rgba: self.background_color
        RoundedRectangle
            size: self.width - 6, self.height - 6
            pos: self.x + 3, self.y + 3
    ''')

    class Card(Factory.ButtonBehavior, Factory.Label):
        background_color = ListProperty()

    def create_random_card():
        return Card(
            text=random.choice('A 2 3 4 5 6 7 8 9 10 J Q K'.split()),
            color=(1, 1, 1, .5, ),
            background_color=kivy.utils.get_random_color())

    def add_random_card(widget, *args):
        widget.add_widget(create_random_card())

    root = Builder.load_string(r'''
FloatLayout:
    GridLayout:
        cols: 2
        rows: 2
        RelativeLayout:
            size_hint: 0.3, 0.3
            id: left_upper
        RelativeLayout:
            size_hint: 0.7, 0.3
            id: right_upper
        RelativeLayout:
            size_hint: 0.3, 0.7
            id: left_lower
        RelativeLayout:
            size_hint: 0.7, 0.7
            id: right_lower
    Widget:
        id: magnet_layer
    ''')
    magnet = MagnetAcrossLayout(
        actual_parent=root.ids.magnet_layer,
        duration=0.5)
    magnet.add_widget(create_random_card())
    root.ids.left_upper.add_widget(magnet)

    def switch_parent(widget, new_parent):
        widget.parent.remove_widget(widget)
        new_parent.add_widget(widget)

    def on_touch_down_handler(root, __):
        ids = 'right_lower right_upper left_upper left_lower'.split()
        switch_parent(magnet, root.ids[random.choice(ids)])
    root.bind(on_touch_down=on_touch_down_handler)

    runTouchApp(root)


if __name__ == "__main__":
    _test()
