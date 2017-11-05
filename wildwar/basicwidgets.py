# -*- coding: utf-8 -*-

__all__ = ('AutoLabel', 'StencilAll', )


import kivy
kivy.require(r'1.10.0')
from kivy.factory import Factory
from kivy.lang import Builder
# from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import (
    NumericProperty, StringProperty, ObjectProperty,
    ListProperty
)

from kivy.garden.magnet import Magnet

import setup_logging
logger = setup_logging.get_logger(__name__)
from adjustfontsizebehavior import AdjustFontsizeBehavior


Builder.load_string(r'''
<NotificationWidget>:
    layout: id_layout
    font_size: 30
    do_scroll_x: False
    do_scroll_y: True
    BoxLayout:
        id: id_layout
        orientation: 'vertical'
        spacing: 1
        size_hint_y: None
        height: self.minimum_height
''')


def fadeout_widget(widget, *, duration=1.3, transition='in_cubic'):
    def on_complete(animation, widget):
        widget.parent.remove_widget(widget)
    animation = Animation(
        duration=duration,
        transition=transition,
        opacity=0)
    animation.bind(on_complete=on_complete)
    animation.start(widget)


class AutoLabel(AdjustFontsizeBehavior, Factory.Label):
    pass


class StencilAll(Factory.StencilView):
    r'''描画だけでなく入力伝達にも領域制限をかけるStencilView'''

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
