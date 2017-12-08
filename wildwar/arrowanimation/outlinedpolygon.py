# -*- coding: utf-8 -*-

__all__ = ('OutlinedPolygon', )

r'''StencilViewとは違って任意の多角形で切り抜ける


例:子Widgetの描画を二等辺三角形で切り抜く

OutlinedPolygon:
    mesh_points: (0, 0, ), (0.5, 1, ), (1, 0, )
    mesh_indices: range(3)
    mesh_mode: 'triangles'
    Button:
        text: 'AAAAAAA'
        font_size: 40
        size: root.size
'''

from itertools import cycle

from kivy.app import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty


Builder.load_string(r'''
<OutlinedPolygon>:
    canvas:
        Color:
            rgba: self.line_color
        Line:
            points: self.line_points
            close: True
            width: self.line_width
            joint_precision: 4
            cap_precision: 4
''')


TEMPLATE_DICT = {
    'arrow1': {
        'line_spoints': (
            0.0, 0.3,
            0.0, 0.7,
            0.7, 0.7,
            0.7, 1.0,
            1.0, 0.5,
            0.7, 0.0,
            0.7, 0.3,
        ),
    },
    'arrow2': {
        'line_spoints': (
            0.0, 0.5,
            0.7, 0.3,
            0.7, 0.0,
            1.0, 0.5,
            0.7, 1.0,
            0.7, 0.7,
        ),
    },
}


class OutlinedPolygon(Factory.Widget):

    line_color = ListProperty((1, 1, 1, 1,))
    line_width = NumericProperty(1)
    line_spoints = ListProperty([])

    line_points = ListProperty([])
    r'''(internal)'''

    @staticmethod
    def create_from_template(name, **kwargs):
        return OutlinedPolygon(**TEMPLATE_DICT[name], **kwargs)

    def __init__(self, **kwargs):
        self._update_points_trigger = \
            Clock.create_trigger(self._update_points, -1)
        super().__init__(**kwargs)

    def _update_points(self, __):
        factors = cycle(self.size)
        self.line_points = [
            value * factor for value, factor in zip(self.line_spoints, factors)]

    def on_spoints(self, __, value):
        self._update_points_trigger()

    def on_size(self, __, value):
        self._update_points_trigger()

    def on_pos(self, __, value):
        self._update_points_trigger()


def _test():
    root = OutlinedPolygon.create_from_template(
        'arrow2', line_color=(0, 1, 0, 1, ), line_width=4)
    runTouchApp(root)


if __name__ == '__main__':
    _test()
