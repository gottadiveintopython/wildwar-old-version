# -*- coding: utf-8 -*-

__all__ = ('play_battle_animation', )


import kivy
kivy.require(r'1.10.0')
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
# from kivy.properties import NumericProperty

from basicwidgets import replace_widget, bring_widget_to_front
from custommodalview import CustomModalViewNoBackground


Builder.load_string(r'''

<BattleAnimationPlayer>:
    Widget:
        id: id_left_dummy
        size_hint: 0.3, 0.5
        pos_hint: {'center_x': 0.25, 'center_y': 0.5, }
    Widget:
        id: id_right_dummy
        size_hint: 0.3, 0.5
        pos_hint: {'center_x': 0.75, 'center_y': 0.5, }
''')


class BattleAnimationPlayer(Factory.RelativeLayout):
    pass


def play_battle_animation(
        *, parent, is_left_attacking_to_right,
        left_uniti_widget, right_uniti_widget, on_complete=None):
    player = BattleAnimationPlayer()
    # player.do_layout()
    ids = player.ids

    left_dummy = ids.id_left_dummy.__ref__()
    right_dummy = ids.id_right_dummy.__ref__()
    left_mag = left_uniti_widget.magnet
    right_mag = right_uniti_widget.magnet
    replace_widget(left_dummy, left_mag)
    replace_widget(right_dummy, right_mag)

    modalview = CustomModalViewNoBackground(
        attach_to=parent, auto_dismiss=False, size_hint=(0.95, 0.6, ), )
    modalview.bind(size=player.setter('size'))
    modalview.add_widget(player)
    modalview.open()

    if is_left_attacking_to_right:
        widgets = (left_uniti_widget, right_uniti_widget, )
    else:
        widgets = (right_uniti_widget, left_uniti_widget, )

    a = widgets[0].uniti
    d = widgets[1].uniti
    bring_widget_to_front(widgets[1])
    bring_widget_to_front(widgets[0])

    def animation_phase5(*args):
        replace_widget(left_dummy, left_mag)
        replace_widget(right_dummy, right_mag)
        modalview.dismiss()
        if on_complete:
            on_complete()

    def animation_phase4(__):
        a_animation = Animation(d=0.2, t='linear', opacity=0) \
            if a.power <= 0 else None
        d_animation = Animation(d=0.2, t='linear', opacity=0) \
            if d.power <= 0 else None
        (a_animation or d_animation).bind(on_complete=animation_phase5)
        if a_animation:
            a_animation.start(widgets[0])
        if d_animation:
            d_animation.start(widgets[1])

    def animation_phase3(*args):
        a.power, d.power = a.power - d.power, d.power - a.power
        Clock.schedule_once(animation_phase4, 0.5)

    def animation_phase2(__):
        if is_left_attacking_to_right:
            animation = Animation(
                d=0.1, t='linear', x=left_uniti_widget.x + 200) + Animation(
                    d=0.15, t='linear', x=left_uniti_widget.x)
        else:
            animation = Animation(
                d=0.1, t='linear', x=right_uniti_widget.x - 200) + Animation(
                    d=0.15, t='linear', x=right_uniti_widget.x)

        animation.bind(on_complete=animation_phase3)
        if is_left_attacking_to_right:
            animation.start(left_uniti_widget)
        else:
            animation.start(right_uniti_widget)

    def animation_phase1(__):
        a.power += a.attack
        a.attack = 0
        d.power += d.defense
        d.defense = 0
        Clock.schedule_once(animation_phase2, 0.5)
    Clock.schedule_once(animation_phase1, 0.5)

