# -*- coding: utf-8 -*-

r"""
"""

__all__ = ('RoundedRectBackground', )

import kivy
kivy.require(r'1.10.0')
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import ListProperty


Builder.load_string(r'''
#:set BORDER_WIDTH 5
#:set SEGMENTS 6

<RoundedRectBackground>:
    canvas.before:
        Color:
            rgba: self.border_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            segments: SEGMENTS
            radius: [(self.width / 4, self.height / 4), ]
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.x + BORDER_WIDTH, self.y + BORDER_WIDTH
            size: self.width - 2 * BORDER_WIDTH, self.height - 2 * BORDER_WIDTH
            segments: SEGMENTS
            radius: [(self.width / 4, self.height / 4), ]
''')


class RoundedRectBackground:

    border_color = ListProperty((1, 1, 1, 1, ))
    background_color = ListProperty((0, 0, 0, 1, ))


Factory.register(
    'RoundedRectBackground',
    cls=RoundedRectBackground)


def _test():
    from kivy.base import runTouchApp

    root = Builder.load_string(r'''

<TestWidget@RoundedRectBackground+Widget>:

TestWidget:
    border_color: .5, .5, 0, 1
    background_color: .2, .2, .2, 1
    ''')

    runTouchApp(root)


if __name__ == "__main__":
    _test()
