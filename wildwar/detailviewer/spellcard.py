# -*- coding: utf-8 -*-

r"""
"""

__all__ = ('SpellCardDetailViewer', )

import kivy
kivy.require(r'1.10.0')
from kivy.factory import Factory
from kivy.lang import Builder
# from kivy.properties import NumericProperty

from basicwidgets import AutoLabel, replace_widget
# import .unitcard


Builder.load_string(r'''
#:set BACKGROUND_COLOR 0, 0, 0, 0.7
#:set BORDER_COLOR 1, 1, 1, 0.2

<SpellCardDetailViewer>:
    BoxLayout:
        spacing: 10
        BoxLayout:
            size_hint_x: 1.2
            orientation: 'vertical'
            spacing: 10
            AutoLabel4CardDetailViewer:
                border_color: BORDER_COLOR
                background_color: BACKGROUND_COLOR
                size_hint_y: 0.2
                text: root.prototype.name
            Widget
                id: id_dummy
        Label4CardDetailViewer:
            border_color: BORDER_COLOR
            background_color: BACKGROUND_COLOR
            padding_x: 10
            id: id_label_detail
            font_size: self.width / 10
            text_size: self.width, None
            text: root.prototype.description
''')


def localize_str(s):
    return s


class SpellCardDetailViewer(Factory.RelativeLayout):

    def __init__(self, *, card, magnet=None, tag_translation_dict, skill_dict, **kwargs):
        self.prototype = card.prototype
        super().__init__(**kwargs)
        replace_widget(self.ids.id_dummy, magnet or card)
