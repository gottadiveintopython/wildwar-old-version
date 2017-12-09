# -*- coding: utf-8 -*-

__all__ = (
    'fadeout_widget', 'AutoLabel', 'StencilAll', 'wrap_function_for_bind',
    'change_label_text_with_fade_animation', 'ModalViewNoBackground',
    'replace_widget', 'bring_widget_to_front',
)

from copy import copy

import kivy
kivy.require(r'1.10.0')
from kivy.factory import Factory
# from kivy.lang import Builder
# from kivy.clock import Clock
from kivy.animation import Animation

try:
    from .adjustfontsizebehavior import AdjustFontsizeBehavior
except ImportError:
    from adjustfontsizebehavior import AdjustFontsizeBehavior


def replace_widget(w1, w2):
    r'''二つのWidgetの位置を入れ替える'''
    widgets = (w1, w2, )
    infos = reversed([
        {
            'parent': w.parent,
            'index': w.parent.children.index(w) if w.parent else None,
            'pos': copy(w.pos),
            'pos_hint': copy(w.pos_hint),
            'size': copy(w.size),
            'size_hint': copy(w.size_hint)}
        for w in widgets])
    for w in widgets:
        parent = w.parent
        if parent:
            parent.remove_widget(w)
    for w, info in zip(widgets, infos):
        w.pos = info['pos']
        w.pos_hint = info['pos_hint']
        w.size = info['size']
        w.size_hint = info['size_hint']
        parent = info['parent']
        if parent:
            parent.add_widget(w, index=info['index'])


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


def _test_replace_widget():
    import random
    from kivy.lang import Builder
    from kivy.app import runTouchApp
    from kivy.garden.magnet import Magnet

    root = Builder.load_string(r'''
BoxLayout:
    GridLayout:
        id: id_grid
        spacing: 10
        padding: 10
        cols: 2
        rows: 2
        Magnet:
            TextInput:
        Magnet:
            Button:
        Magnet:
            Button:
        Magnet:
            TextInput:
    AnchorLayout:
        id: id_anchor
        Magnet:
            size_hint: None, None
            Widget:
    ''')

    # 親を持たないWidget同士の入れ替え
    replace_widget(Factory.Button(), Factory.Button())

    # 親を持つWidget と 持たないWidget の入れ替え
    replace_widget(
        root.ids.id_anchor.children[0].children[0],
        Factory.Button(text='button'))

    # 親を持つWidget同士の入れ替え
    def on_touch_down(root, touch):
        replace_widget(
            root.ids.id_anchor.children[0],
            random.choice(root.ids.id_grid.children))
    root.bind(on_touch_down=on_touch_down)
    runTouchApp(root)


if __name__ == '__main__':
    _test_replace_widget()
