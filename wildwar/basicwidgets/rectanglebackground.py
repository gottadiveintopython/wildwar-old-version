# -*- coding: utf-8 -*-

r"""
"""

__all__ = ('RectangleBackground', )

import kivy
kivy.require(r'1.10.0')
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import ListProperty


Builder.load_string(r'''
#:set BORDER_WIDTH 2

<RectangleBackground>:
    canvas.before:
        Color:
            rgba: self.border_color
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.x + BORDER_WIDTH, self.y + BORDER_WIDTH
            size: self.width - 2 * BORDER_WIDTH, self.height - 2 * BORDER_WIDTH
''')


class RectangleBackground:

    border_color = ListProperty((1, 1, 1, 1, ))
    background_color = ListProperty((0, 0, 0, 1, ))


Factory.register(
    'RectangleBackground',
    cls=RectangleBackground)


def _test():
    from kivy.base import runTouchApp

    root = Builder.load_string(r'''

<TestWidget@RectangleBackground+Widget>:

FloatLayout:
    TestWidget:
        size_hint: 0.5, 0.5
        pos: 30, 30
        border_color: .5, .5, 0, 1
        background_color: .2, .2, .2, 1
    ''')

    runTouchApp(root)


if __name__ == "__main__":
    _test()
