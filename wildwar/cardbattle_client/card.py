# -*- coding: utf-8 -*-

__all__ = ('UnknownCard', 'SpellCard', 'UnitCard', )

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

<UnknownCard>:
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        RoundedRectangle:
            size: self.width, self.height
            pos: 0, 0
        RoundedRectangle:
            source: 'back_side.jpg'
            size: self.width - 4, self.height - 4
            pos: 2, 2

<SpellCard,UnitCard>:
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        RoundedRectangle:
            size: self.width, self.height
            pos: 0, 0
        Color:
            rgba: self.background_color
        RoundedRectangle:
            size: self.width - 4, self.height - 4
            pos: 2, 2
    canvas.after:
        Color:
            rgba: OVERLAY_COLOR_DICT[self.state]
        RoundedRectangle:
            size: self.width, self.height
            pos: self.pos

<SpellCard>:
    Image:
        source: root.imagefile
    AutoLabel:
        pos_hint: {'x': 0, 'top': 1}
        size_hint: 0.2, 0.2
        bold: True
        text: str(root.prototype.cost)

<UnitCard>:
    Image:
        source: root.imagefile
    AutoLabel:
        pos_hint: {'x': 0, 'top': 1}
        size_hint: 0.2, 0.2
        bold: True
        text: str(root.prototype.cost)
    BoxLayout:
        size_hint: 1, 0.2
        AutoLabel:
            bold: True
            text:
                (str(root.prototype.attack)
                if root.prototype.attack != 0 else '')
        AutoLabel:
            bold: True
            text: str(root.prototype.power)
        AutoLabel:
            bold: True
            text:
                (str(root.prototype.defense)
                if root.prototype.defense != 0 else '')

""")


class UnknownCard(Factory.RelativeLayout):
    pass


class UnitCard(Factory.ButtonBehavior, Factory.RelativeLayout):
    id = StringProperty()
    prototype = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))


class SpellCard(Factory.ButtonBehavior, Factory.RelativeLayout):
    id = StringProperty()
    prototype = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))
