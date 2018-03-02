# -*- coding: utf-8 -*-

__all__ = ('UnitInstanceWidget', )

import kivy
kivy.require(r'1.10.0')
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.properties import (
    ObjectProperty, NumericProperty, StringProperty, ListProperty,
)

# import setup_logging
# logger = setup_logging.get_logger(__name__)
from basicwidgets import AutoLabel


Builder.load_string(r"""
#:kivy 1.10.0
#:set OVERLAY_COLOR_DICT { r'normal': [0, 0, 0, 0], r'down': [1, 1, 1, 0.15], }

<UnitInstanceWidget>:
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: 0, 0
    canvas.after:
        Color:
            rgba: OVERLAY_COLOR_DICT[self.state]
        RoundedRectangle:
            size: self.size
            pos: self.pos
    Image:
        source: root.imagefile
    AutoLabel:
        pos_hint: {'x': 0, 'top': 1, }
        size_hint: 0.2, 0.2
        # bold: True
        outline_color: 0, 0, 0, 1,
        outline_width: 1
        text: str(root.uniti.cost)
    Image:
        pos_hint: {'right': 1, 'top': 1, }
        size_hint: None, None
        size: self.texture_size
        source: 'icon_lock.png'
        opacity: 0 if root.uniti.n_turns_until_movable == 0 else 1
    BoxLayout:
        size_hint: 1, 0.2
        AutoLabel:
            # bold: True
            outline_color: 0, 0, 0, 1,
            outline_width: 1
            text:
                (str(root.uniti.attack)
                if root.uniti.attack != 0 else '')
        AutoLabel:
            # bold: True
            outline_color: 0, 0, 0, 1,
            outline_width: 1
            text: str(root.uniti.power)
        AutoLabel:
            # bold: True
            outline_color: 0, 0, 0, 1,
            outline_width: 1
            text:
                (str(root.uniti.defense)
                if root.uniti.defense != 0 else '')

""")


class UnitInstanceWidget(Factory.ButtonBehavior, Factory.RelativeLayout):
    magnet = ObjectProperty(None, allownone=True)
    klass = StringProperty('UnitInstanceWidget')
    id = StringProperty()
    uniti = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))
