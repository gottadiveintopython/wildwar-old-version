# -*- coding: utf-8 -*-

from kivy.event import EventDispatcher
from kivy.properties import (
    NumericProperty, StringProperty, ReferenceListProperty, ObjectProperty,
    ListProperty,
)

# class Card(EventDispatcher):
#     id = StringProperty()
#     klass = ObjectProperty(CardType.NONE)


class UnitPrototype(EventDispatcher):
    id = StringProperty()
    name = StringProperty()
    cost = NumericProperty()
    power = NumericProperty()
    attack = NumericProperty()
    defense = NumericProperty()
    stats = ReferenceListProperty(power, attack, defense)
    skills = ListProperty()
    tags = ListProperty()


class UnitInstance(EventDispatcher):
    id = StringProperty()
    prototype = ObjectProperty()  # UnitPrototypr
    player = ObjectProperty()  # Player
    n_turns_until_movable = NumericProperty()
    power = NumericProperty()
    attack = NumericProperty()
    defense = NumericProperty()
    stats = ReferenceListProperty(power, attack, defense)
    o_power = NumericProperty()
    o_attack = NumericProperty()
    o_defense = NumericProperty()
    o_stats = ReferenceListProperty(o_power, o_attack, o_defense)

    @property
    def color(self):
        return self.player.color


for _name in r'name skills tags cost'.split():
    setattr(UnitInstance, _name, property(
        lambda self, _name=_name: getattr(self.prototype, _name)
    ))
