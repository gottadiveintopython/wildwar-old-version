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

<UnitInstanceWidget>:
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            size: self.size
            pos: 0, 0
    Image:
        source: root.imagefile
    AutoLabel:
        pos_hint: {'x': 0, 'top': 1, }
        size_hint: 0.2, 0.2
        bold: True
        text: str(root.unitinstance.cost)
    Image:
        pos_hint: {'right': 1, 'top': 1, }
        size_hint: None, None
        size: self.texture_size
        source: '' if root.unitinstance.n_turns_until_movable == 0 else 'icon_lock.png'
    BoxLayout:
        size_hint: 1, 0.2
        AutoLabel:
            bold: True
            text:
                (str(root.unitinstance.attack)
                if root.unitinstance.attack != 0 else '')
        AutoLabel:
            bold: True
            text: str(root.unitinstance.power)
        AutoLabel:
            bold: True
            text:
                (str(root.unitinstance.defense)
                if root.unitinstance.defense != 0 else '')

""")


class UnitInstanceWidget(Factory.RelativeLayout):
    magnet = ObjectProperty(None, allownone=True)
    id = StringProperty()
    unitinstance = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))
