# -*- coding: utf-8 -*-

r"""
TefudaLayout
==============

カードゲームで見かける、カードが少しずつ重なりながら横に並んでるようなLayout
"""

__all__ = ('TefudaLayout')

import kivy
kivy.require(r'1.10.0')
from kivy.uix.layout import Layout
from kivy.properties import (
    NumericProperty,
)


class TefudaLayout(Layout):

    child_aspect_ratio = NumericProperty(0.7)

    def __init__(self, **kwargs):
        super(TefudaLayout, self).__init__(**kwargs)

        self.bind(
            parent=self._trigger_layout,
            children=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def do_layout(self, *args):
        # self.childrenに入っている子は加えた順とは逆な為、加えた順に変換
        children = list(reversed(self.children))

        n_children = len(children)

        if n_children == 0:
            return

        # 子の大きさは全てこの大きさに強制する(その方がLayoutの計算が楽だから)
        force_child_size = (self.height * self.child_aspect_ratio, self.height)

        # 横の余白の合計値。この値は負にもなりえる。
        sum_margin_x = self.width - (force_child_size[0] * n_children)

        # print('force_child_size: ', force_child_size)
        # print('sum_margin_x: ', sum_margin_x)

        # 横幅に余裕がある時は、子を隙間を空けて並べる
        if sum_margin_x > 0:
            spacing = sum_margin_x / (n_children + 1)
            next_x = self.x + spacing
        # 横幅に余裕が無い時は、子を少し重ねて配置する
        else:
            if n_children == 1:
                spacing = 0
            else:
                spacing = sum_margin_x / (n_children - 1)
            next_x = self.x
        offset = spacing + force_child_size[0]

        # print('offset: ', offset)
        # print('spacing: ', spacing)
        # print('next_x: ', next_x)

        for child in children:
            child.size = force_child_size
            child.pos = (next_x, self.y)
            next_x += offset

        # import pdb;pdb.set_trace()


def _test():
    import functools
    import random
    from kivy.base import runTouchApp
    from kivy.lang import Builder
    from kivy.factory import Factory
    from kivy.properties import ListProperty
    import kivy.utils

    root = Builder.load_string(r'''
<Card>:
    font_size: 100
    canvas.before:
        Color:
            rgba: .3, .3, .3, 1
        RoundedRectangle
            size: self.size
            pos: self.pos
        Color:
            rgba: self.background_color
        RoundedRectangle
            size: self.width - 6, self.height - 6
            pos: self.x + 3, self.y + 3

BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        spacing: 20
        orientation: 'horizontal'
        size_hint_y: 0.4
        TefudaLayout:
            id: id_opponent_tefuda
            size_hint_x: 0.8
            pop_direction: 'down'
        Button:
            id: id_opponent_button
            text: 'draw card'
            size_hint_x: 0.2
    FloatLayout:
        size_hint_y: 0.2
    BoxLayout:
        spacing: 20
        orientation: 'horizontal'
        size_hint_y: 0.4
        TefudaLayout:
            id: id_self_tefuda
            size_hint_x: 0.8
            pop_direction: 'up'
        Button:
            id: id_self_button
            text: 'draw card'
            size_hint_x: 0.2
    ''')

    class Card(Factory.ButtonBehavior, Factory.Label):

        background_color = ListProperty()

    def create_random_card():
        return Card(
            text=random.choice(r'A 2 3 4 5 6 7 8 9 10 J Q K'.split()),
            color=(1, 1, 1, .5, ),
            background_color=kivy.utils.get_random_color())

    def add_random_card_to_layout(__, *, layout):
        layout.add_widget(create_random_card())

    root.ids.id_self_button.bind(
        on_press=functools.partial(
            add_random_card_to_layout,
            layout=root.ids.id_self_tefuda))

    root.ids.id_opponent_button.bind(
        on_press=functools.partial(
            add_random_card_to_layout,
            layout=root.ids.id_opponent_tefuda))

    runTouchApp(root)


if __name__ == "__main__":
    _test()
