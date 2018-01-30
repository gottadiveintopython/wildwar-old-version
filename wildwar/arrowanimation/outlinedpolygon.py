# -*- coding: utf-8 -*-

__all__ = ('OutlinedPolygon', )

r'''内側を塗りつぶさない多角形を簡単に表示する為のWidget


例: 二等辺三角形を表示するWidget

OutlinedPolygon:
    color: 1, 1, 1, 1
    line_points: 0, 0, 0.5, 1, 1, 0,  # x1, y1, x2, y2, ...
    line_width: 1
'''

import itertools

from kivy.app import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty


Builder.load_string(r'''
<OutlinedPolygon>:
    canvas:
        Color:
            rgba: self.color
        Line:
            points: self._line_points
            close: True
            width: self.line_width
            joint_precision: 4
            cap_precision: 4
''')


TEMPLATE_DICT = {
    'arrow1': {
        'line_points': (
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
        'line_points': (
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

    color = ListProperty((1, 1, 1, 1,))
    line_width = NumericProperty(1)
    line_points = ListProperty([])

    _line_points = ListProperty([])
    r'''(internal)'''

    @staticmethod
    def create_from_template(name, **kwargs):
        return OutlinedPolygon(**TEMPLATE_DICT[name], **kwargs)

    def __init__(self, **kwargs):
        self._update_points_trigger = \
            Clock.create_trigger(self._update_points, -1)
        super().__init__(**kwargs)

    def _update_points(self, __):
        self._line_points = [
            value * factor + offset for value, factor, offset in zip(
                self.line_points,
                itertools.cycle(self.size),
                itertools.cycle(self.pos))]

    def on_spoints(self, __, value):
        self._update_points_trigger()

    def on_size(self, __, value):
        self._update_points_trigger()

    def on_pos(self, __, value):
        self._update_points_trigger()


def _test():
    root = Factory.BoxLayout(orientation='vertical')
    root.add_widget(OutlinedPolygon.create_from_template(
        'arrow2', color=(0, 1, 0, 1, ), line_width=4))
    root.add_widget(Builder.load_string(r'''
OutlinedPolygon:
    color: 1, 1, 1, 1
    line_points: 0, 0, 0.5, 1, 1, 0,
    line_width: 4
'''))
    runTouchApp(root)


if __name__ == '__main__':
    _test()
