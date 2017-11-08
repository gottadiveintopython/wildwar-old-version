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

<UnknownCard>:
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        RoundedRectangle
            size: self.width, self.height
            pos: 0, 0
        RoundedRectangle
            source: 'back_side.jpg'
            size: self.width - 4, self.height - 4
            pos: 2, 2

<SpellCard,UnitCard>:
    canvas.before:
        Color:
            rgba: 0.3, 0.3, 0.3, 1
        RoundedRectangle
            size: self.width, self.height
            pos: 0, 0
        Color:
            rgba: self.background_color
        RoundedRectangle
            size: self.width - 4, self.height - 4
            pos: 2, 2

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
            id: id_label_attack
            text: str(root.attack) if root.attack != 0 else ''
        AutoLabel:
            bold: True
            id: id_label_power
            text: str(root.power)
        AutoLabel:
            bold: True
            id: id_label_defense
            text: str(root.defense) if root.defense != 0 else ''

""")


class UnknownCard(Factory.RelativeLayout):
    pass


class UnitCard(Factory.RelativeLayout):

    prototype = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))
    power = NumericProperty()
    attack = NumericProperty()
    defense = NumericProperty()

    def __init__(self, *, prototype, **kwargs):
        super().__init__(prototype=prototype, **kwargs)
        self.power = prototype.power
        self.attack = prototype.attack
        self.defense = prototype.defense


for _name in r'id name skills tags cost'.split():
    setattr(UnitCard, _name, property(
        lambda self, _name=_name: getattr(self.prototype, _name)
    ))


class SpellCard(Factory.RelativeLayout):

    prototype = ObjectProperty()
    imagefile = StringProperty()
    background_color = ListProperty((0, 0, 0, 0, ))


for _name in r'id name cost description'.split():
    setattr(SpellCard, _name, property(
        lambda self, _name=_name: getattr(self.prototype, _name)
    ))
