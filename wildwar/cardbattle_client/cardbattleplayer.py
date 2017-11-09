# -*- coding: utf-8 -*-

__all__ = ('Player', 'CardBattlePlayer', )


import kivy
kivy.require(r'1.10.0')
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.utils import get_color_from_hex
# from kivy.factory import Factory
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty,
)
# from kivy.graphics import Color, Line
from kivy.animation import Animation

import setup_logging
logger = setup_logging.get_logger(__name__)
from basicwidgets import (
    AutoLabel,
    change_label_text_with_fade_animation, wrap_function_for_bind,
)
from tefudalayout import TefudaLayout


Builder.load_string(r"""
#:kivy 1.10.0

<CardBattlePlayer>:
    canvas.before:
        Color:
            rgba: .2, .2, .2, 1
        Line:
            rectangle: [*self.pos, *self.size]
    BoxLayout:
        orientation: 'horizontal'
        pos_hint: {'x': 0, 'y': 0}
        FloatLayout:
            size_hint_x: 0.8
            TefudaLayout:
                id: id_tefuda
                size_hint: 0.9, 0.9
                child_aspect_ratio: 0.7
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        BoxLayout:
            size_hint_x: 0.2
            orientation: 'vertical'
            # id: id_status
            AutoLabel:
                size_hint_y: 1.7
                # bold: True
                text: root.id
            BoxLayout:
                Image:
                    source: 'icon_cost.png'
                AutoLabel:
                    id: id_label_cost
                    text: '{}/{}'.format(str(root.cost), str(root.max_cost))
            BoxLayout:
                Image:
                    source: 'icon_deck.png'
                AutoLabel:
                    id: id_label_deck
                    text: str(root.n_cards_in_deck)
""")


def let_label_animate(label, duration=0.2):
    r'''内部で呼び出している関数の名前が長いので、この関数を用意した'''
    return wrap_function_for_bind(
        change_label_text_with_fade_animation,
        label, duration=duration)


class Player(Factory.EventDispatcher):
    id = StringProperty()
    cost = NumericProperty()
    max_cost = NumericProperty()
    n_cards_in_deck = NumericProperty()
    tefuda = ListProperty()
    color = ListProperty()


class CardBattlePlayer(Factory.FloatLayout):
    id = StringProperty()
    cost = NumericProperty()
    max_cost = NumericProperty()
    n_cards_in_deck = NumericProperty()
    color = ListProperty()

    def __init__(self, *, player, **kwargs):
        super().__init__(
            id=player.id,
            cost=player.cost,
            max_cost=player.max_cost,
            n_cards_in_deck=player.n_cards_in_deck,
            color=player.color,
            **kwargs)
        player.bind(
            id=self.setter('id'),
            cost=self.on_cost_changed,
            max_cost=self.on_cost_changed,
            n_cards_in_deck=let_label_animate(self.ids.id_label_deck),
            color=self.setter('color'))

    def on_cost_changed(self, player, value):
        label = self.ids.id_label_cost
        self.cost = player.cost
        self.max_cost = player.max_cost
        animation = getattr(self, '_cost_animation', None)
        # costが最大値を上回っていないなら白色で非点滅
        if player.cost <= player.max_cost:
            if animation is not None:
                label.color = get_color_from_hex('#ffffff')
                animation.stop(label)
                self._cost_animation = None
        # costが最大値を上回っているなら赤色で点滅
        elif animation is None:
            label.color = get_color_from_hex('#ff2222')
            animation = Animation(
                opacity=0,
                duration=0.8,
                transition='in_cubic') + Animation(
                    opacity=1,
                    duration=0.8,
                    transition='out_cubic')
            animation.repeat = True
            animation.start(label)
            self._cost_animation = animation

    # def on_n_cards_in_deck_changed(self, player, value):
    #     label = self.ids.id_label_deck

    #     def on_fadeout_complete(animation, widget):
    #         self.n_cards_in_deck = value
    #         animation_fadein = Animation(
    #             opacity=1,
    #             duration=0.1,
    #             transition='linear')
    #         animation_fadein.start(label)

    #     animation_fadeout = Animation(
    #         opacity=0,
    #         duration=0.1,
    #         transition=r'linear')
    #     animation_fadeout.bind(on_complete=on_fadeout_complete)
    #     animation_fadeout.start(label)
