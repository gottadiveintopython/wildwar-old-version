# -*- coding: utf-8 -*-

__all__ = ('TurnEndButton', )

if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.abspath('..'))

import kivy
kivy.require(r'1.10.0')
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.animation import Animation
from kivy.properties import (
    NumericProperty, ListProperty,
)

import setup_logging
logger = setup_logging.get_logger(__name__)
from basicwidgets import AutoLabel

Builder.load_string(r"""
#:kivy 1.10.0

<TurnEndButton>:
    text: ' Turn \n End '
    halign: 'center'
    disabled: True
    background_color: 1, 1, 1, self.background_opacity
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            segments: 4
            radius: [(self.width / 4, self.height / 4), ]
""")


class TurnEndButton(Factory.ButtonBehavior, AutoLabel):
    background_color = ListProperty((1, 1, 1, 0, ))
    background_opacity = NumericProperty(0)

    def on_disabled(self, __, value):
        # print('on_disabled', value)
        if value:
            self.cancel_animation()
        else:
            self.cancel_animation()
            self.start_animation()

    def cancel_animation(self):
        animation = getattr(self, '_animation', None)
        if animation is not None:
            animation.cancel(self)
        self.background_opacity = 0

    def start_animation(self):
        animation = Animation(
            duration=1,
            transition='in_cubic',
            background_opacity=0.3) + Animation(
                duration=1,
                transition='out_cubic',
                background_opacity=0)
        animation.repeat = True
        animation.start(self)
        self._animation = animation


def _test():
    from kivy.app import runTouchApp
    from kivy.resources import resource_add_path
    resource_add_path('../data/font')
    import set_default_font_to_japanese
    set_default_font_to_japanese.apply()

    root = Builder.load_string(r'''
BoxLayout:
    TurnEndButton:
        id: id_turnendbutton
    Button:
        text: 'disable'
        on_press: id_turnendbutton.disabled = True
    Button:
        text: 'enable'
        on_press: id_turnendbutton.disabled = False
    ''')
    runTouchApp(root)


if __name__ == '__main__':
    _test()
