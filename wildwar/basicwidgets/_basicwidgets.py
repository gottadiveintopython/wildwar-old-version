# -*- coding: utf-8 -*-

__all__ = (
    'fadeout_widget', 'AutoLabel', 'StencilAll', 'wrap_function_for_bind',
    'change_label_text_with_fade_animation', 'ModalViewNoBackground',
    'replace_widget', 'bring_widget_to_front',
)

import kivy
kivy.require(r'1.10.0')
from kivy.factory import Factory
# from kivy.lang import Builder
# from kivy.clock import Clock
from kivy.animation import Animation

from .adjustfontsizebehavior import AdjustFontsizeBehavior


def replace_widget(old, new):
    r'''old.parentは非None、new.parentはNoneでなければならない'''
    assert old.parent is not None
    assert new.parent is None
    new.pos = old.pos
    new.pos_hint = old.pos_hint
    new.size = old.size
    new.size_hint = old.size_hint
    parent = old.parent
    index = parent.children.index(old)
    parent.remove_widget(old)
    parent.add_widget(new, index=index)


def bring_widget_to_front(widget):
    parent = widget.parent
    parent.remove_widget(widget)
    parent.add_widget(widget)


def fadeout_widget(widget, *, duration=1.3, transition='in_cubic'):
    def on_complete(animation, widget):
        widget.parent.remove_widget(widget)
    animation = Animation(
        duration=duration,
        transition=transition,
        opacity=0)
    animation.bind(on_complete=on_complete)
    animation.start(widget)


def change_label_text_with_fade_animation(label, *, value, duration):
    r'''Labelのtextをfade-out,fade-inさせながら書き換える'''

    def on_fadeout_complete(animation, label):
        label.text = str(value)
        animation_fadein = Animation(
            opacity=1,
            duration=duration / 2,
            transition='linear')
        animation_fadein.start(label)

    animation_fadeout = Animation(
        opacity=0,
        duration=duration / 2,
        transition=r'linear')
    animation_fadeout.bind(on_complete=on_fadeout_complete)
    animation_fadeout.start(label)


def wrap_function_for_bind(function, *args, **kwargs):
    r'''functionをbindのkeyword引数の値に渡せる形に変換する。

    functionは仮引数value(Propertyの新しい値が渡される)を持っている必要がある'''
    return lambda __, value: function(*args, value=value, **kwargs)


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


class ModalViewNoBackground(Factory.ModalView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas.clear()
        self.canvas.before.clear()
        self.canvas.after.clear()
